"""Security controls: path traversal validation, input sanitization, and security headers."""

import ipaddress
import os
import re
from urllib.parse import urlparse

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from src.evalforge.core.errors import PayloadTooLargeError, SecurityViolationError


def sanitize_filename(filename: str) -> str:
    """Strip directory components, null bytes, and unsafe characters from filenames."""
    # Strip paths
    clean = os.path.basename(filename)
    # Remove null bytes and non-alphanumeric/safe chars
    clean = re.sub(r"[^\w\.\-_]", "_", clean)
    return clean or "unnamed_file"


def validate_path_safety(target_path: str, base_dir: str | None = None) -> str:
    """Ensure target_path does not escape base directory via directory traversal."""
    if "\0" in target_path:
        raise SecurityViolationError("Path contains prohibited null byte character.")

    norm_path = os.path.abspath(target_path)
    if base_dir:
        norm_base = os.path.abspath(base_dir)
        if not norm_path.startswith(norm_base):
            raise SecurityViolationError(
                f"Path traversal detected: '{target_path}' attempts to escape boundary '{base_dir}'."
            )

    return norm_path


def enforce_content_length(content_length: int | None, max_allowed_bytes: int) -> None:
    """Verify request content-length against configured maximum bytes limit."""
    if content_length and content_length > max_allowed_bytes:
        raise PayloadTooLargeError(
            f"Payload length ({content_length} bytes) exceeds maximum limit of {max_allowed_bytes} bytes.",
            max_bytes=max_allowed_bytes,
        )


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Enforces standard HTTP security defense headers on all responses."""

    async def dispatch(self, request: Request, call_next: object) -> Response:
        response: Response = await call_next(request)  # type: ignore[operator]
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        return response


PRIVATE_HOSTNAMES = {
    "localhost",
    "metadata.google.internal",
    "metadata.google.internal.",
    "instance-data",
}

METADATA_IPS = {
    ipaddress.ip_address("169.254.169.254"),
    ipaddress.ip_address("169.254.170.2"),
    ipaddress.ip_address("100.100.100.200"),
    ipaddress.ip_address("fd00:ec2::254"),
}


def _is_disallowed_address(address: ipaddress.IPv4Address | ipaddress.IPv6Address) -> bool:
    """Return True if an address falls into a range that must not be requestable by default."""
    return bool(
        address.is_private
        or address.is_loopback
        or address.is_link_local
        or address.is_reserved
        or address.is_multicast
        or address.is_unspecified
    )


def resolve_host_addresses(hostname: str) -> set[ipaddress.IPv4Address | ipaddress.IPv6Address]:
    """Resolve a hostname to its IPv4/IPv6 addresses, rejecting failures."""
    import socket

    try:
        return {ipaddress.ip_address(hostname.strip("[]"))}
    except ValueError:
        pass

    try:
        infos = socket.getaddrinfo(hostname, None, proto=socket.IPPROTO_TCP)
    except socket.gaierror as exc:
        raise SecurityViolationError(
            f"Hostname '{hostname}' could not be resolved: {exc}"
        ) from exc

    addresses = set()
    for info in infos:
        try:
            addresses.add(ipaddress.ip_address(info[4][0]))
        except ValueError:
            continue
    if not addresses:
        raise SecurityViolationError(f"Hostname '{hostname}' resolved to no usable addresses.")
    return addresses


def validate_safe_url(
    url: str,
    allowed_hosts: list[str] | None = None,
    allow_private: bool = False,
) -> str:
    """Validate a provider endpoint URL against SSRF, metadata, and DNS-rebinding risks.

    DNS names are resolved and every resolved address is checked, so a hostname
    that points at a loopback or metadata address is rejected even if the literal
    hostname looks benign.
    """
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise SecurityViolationError(f"Disallowed URL scheme: {parsed.scheme}")
    if parsed.username or parsed.password:
        raise SecurityViolationError("Credentials embedded in provider URLs are not allowed.")

    hostname = (parsed.hostname or "").lower()
    if not hostname:
        raise SecurityViolationError("URL has empty or invalid hostname")

    if hostname.rstrip(".") in {h.rstrip(".") for h in PRIVATE_HOSTNAMES}:
        if not allow_private:
            raise SecurityViolationError(
                f"Hostname '{hostname}' is a local/metadata endpoint and is not permitted."
            )

    allowed = {h.lower() for h in (allowed_hosts or [])}
    if allowed and hostname not in allowed:
        raise SecurityViolationError(f"Hostname '{hostname}' is not in the allowed destination list.")

    for address in resolve_host_addresses(hostname):
        if address in METADATA_IPS:
            raise SecurityViolationError("Targeting cloud metadata services is strictly prohibited.")
        if not allow_private and _is_disallowed_address(address):
            raise SecurityViolationError(
                f"Hostname '{hostname}' resolves to non-public address '{address}', which is prohibited."
            )

    return url


class RequestBodyLimitMiddleware(BaseHTTPMiddleware):
    """Reject requests whose declared body exceeds the configured hard limit."""

    def __init__(self, app: object, max_body_bytes: int):
        super().__init__(app)  # type: ignore[arg-type]
        self.max_body_bytes = max_body_bytes

    async def dispatch(self, request: Request, call_next: object) -> Response:
        content_length = request.headers.get("content-length")
        if content_length:
            try:
                declared = int(content_length)
            except ValueError:
                return Response(
                    content='{"error":{"code":"INVALID_CONTENT_LENGTH","message":"Invalid Content-Length header."}}',
                    status_code=400,
                    media_type="application/json",
                )
            if declared > self.max_body_bytes:
                return Response(
                    content=(
                        '{"error":{"code":"PAYLOAD_TOO_LARGE","message":"Request body exceeds the '
                        f'configured limit of {self.max_body_bytes} bytes."}}}}'
                    ),
                    status_code=413,
                    media_type="application/json",
                )
        return await call_next(request)  # type: ignore[operator]


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Fixed-window per-client rate limiter for API routes.

    This is intentionally in-process: it protects a single-instance deployment.
    Multi-worker deployments should also enforce limits at the reverse proxy.
    """

    def __init__(self, app: object, requests_per_minute: int = 240):
        super().__init__(app)  # type: ignore[arg-type]
        self.limit = max(1, requests_per_minute)
        self.window_seconds = 60.0
        self._buckets: dict[str, tuple[float, int]] = {}

    def _client_key(self, request: Request) -> str:
        forwarded = request.headers.get("x-forwarded-for")
        client = (
            forwarded.split(",")[0].strip()
            if forwarded
            else (request.client.host if request.client else "unknown")
        )
        # Bucket per endpoint group so a single busy route cannot exhaust the
        # budget for unrelated endpoints on the same client.
        parts = [p for p in request.url.path.split("/") if p]
        group = "/".join(parts[:3])
        return f"{client}:{group}"

    async def dispatch(self, request: Request, call_next: object) -> Response:
        import time

        path = request.url.path
        if not path.startswith("/api") or path.startswith(("/api/health", "/api/v1/health")):
            return await call_next(request)  # type: ignore[operator]

        now = time.monotonic()
        key = self._client_key(request)
        window_start, count = self._buckets.get(key, (now, 0))
        if now - window_start >= self.window_seconds:
            window_start, count = now, 0
        count += 1
        self._buckets[key] = (window_start, count)

        if len(self._buckets) > 10000:
            cutoff = now - self.window_seconds
            self._buckets = {k: v for k, v in self._buckets.items() if v[0] >= cutoff}

        if count > self.limit:
            retry_after = max(1, int(self.window_seconds - (now - window_start)))
            return Response(
                content=(
                    '{"error":{"code":"RATE_LIMITED","message":"Too many requests. '
                    f'Retry after {retry_after} seconds."}}}}'
                ),
                status_code=429,
                media_type="application/json",
                headers={"Retry-After": str(retry_after)},
            )

        response = await call_next(request)  # type: ignore[operator]
        response.headers["X-RateLimit-Limit"] = str(self.limit)
        response.headers["X-RateLimit-Remaining"] = str(max(0, self.limit - count))
        return response


class BearerAuthMiddleware(BaseHTTPMiddleware):
    """Optional shared-secret bearer authentication for self-hosted deployments."""

    def __init__(self, app: object, token: str):
        super().__init__(app)  # type: ignore[arg-type]
        self.token = token

    async def dispatch(self, request: Request, call_next: object) -> Response:
        import hmac

        path = request.url.path
        if request.method == "OPTIONS" or not path.startswith("/api"):
            return await call_next(request)  # type: ignore[operator]
        exempt = (
            "/api/health",
            "/api/v1/health",
            "/api/health/live",
            "/api/health/ready",
            "/api/v1/health/live",
            "/api/v1/health/ready",
            "/api/openapi.json",
            "/api/docs",
            "/api/redoc",
        )
        if path.rstrip("/") in {p.rstrip("/") for p in exempt}:
            return await call_next(request)  # type: ignore[operator]

        header = request.headers.get("authorization", "")
        scheme, _, supplied = header.partition(" ")
        if scheme.lower() != "bearer" or not hmac.compare_digest(supplied.strip(), self.token):
            return Response(
                content='{"error":{"code":"UNAUTHORIZED","message":"A valid bearer token is required."}}',
                status_code=401,
                media_type="application/json",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return await call_next(request)  # type: ignore[operator]
