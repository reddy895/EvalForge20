"""Security controls: path traversal validation, input sanitization, and security headers."""

import os
import re

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
