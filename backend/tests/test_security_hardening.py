"""Security boundary tests for URL validation and HTTP guardrail middleware."""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from starlette.responses import PlainTextResponse

from src.evalforge.core.errors import SecurityViolationError
from src.evalforge.core.security import (
    BearerAuthMiddleware,
    RateLimitMiddleware,
    RequestBodyLimitMiddleware,
    sanitize_filename,
    validate_safe_url,
)


@pytest.mark.security
@pytest.mark.parametrize(
    "url",
    [
        "http://169.254.169.254/latest/meta-data/",
        "http://127.0.0.1:8000/internal",
        "http://10.0.0.5/admin",
        "http://[::1]/internal",
        "file:///etc/passwd",
        "gopher://example.com/",
    ],
)
def test_ssrf_rejects_private_and_metadata_targets(url: str) -> None:
    with pytest.raises(SecurityViolationError):
        validate_safe_url(url, allow_private=False)


@pytest.mark.security
def test_ssrf_allows_local_targets_when_explicitly_permitted() -> None:
    assert validate_safe_url("http://127.0.0.1:11434", allow_private=True)
    assert validate_safe_url("http://localhost:11434", allow_private=True)


@pytest.mark.security
def test_ssrf_rejects_embedded_credentials() -> None:
    with pytest.raises(SecurityViolationError):
        validate_safe_url("http://user:pass@example.com/v1")


@pytest.mark.security
def test_ssrf_enforces_host_allowlist() -> None:
    with pytest.raises(SecurityViolationError):
        validate_safe_url("https://api.example.com/v1", allowed_hosts=["allowed.example.org"])


@pytest.mark.security
def test_sanitize_filename_blocks_traversal() -> None:
    assert sanitize_filename("../../etc/passwd") == "passwd"
    assert sanitize_filename("..\\..\\windows\\system32") != "..\\..\\windows\\system32"


def _build_app_with_middleware(middleware: object, **kwargs: object) -> FastAPI:
    app = FastAPI()

    @app.get("/api/value")
    async def value() -> PlainTextResponse:
        return PlainTextResponse("ok")

    @app.get("/api/health")
    async def health() -> PlainTextResponse:
        return PlainTextResponse("healthy")

    app.add_middleware(middleware, **kwargs)  # type: ignore[arg-type]
    return app


@pytest.mark.security
def test_request_body_limit_rejects_oversized_declared_body() -> None:
    app = _build_app_with_middleware(RequestBodyLimitMiddleware, max_body_bytes=10)
    with TestClient(app) as client:
        response = client.post("/api/value", content=b"x" * 100)
        assert response.status_code == 413


@pytest.mark.security
def test_rate_limit_returns_429_and_headers() -> None:
    app = _build_app_with_middleware(RateLimitMiddleware, requests_per_minute=2)
    with TestClient(app) as client:
        assert client.get("/api/value").status_code == 200
        assert client.get("/api/value").status_code == 200
        blocked = client.get("/api/value")
        assert blocked.status_code == 429
        assert blocked.headers["Retry-After"]


@pytest.mark.security
def test_optional_bearer_auth_protects_api_but_not_health() -> None:
    app = _build_app_with_middleware(BearerAuthMiddleware, token="secret-token")
    with TestClient(app) as client:
        assert client.get("/api/health").status_code == 200
        assert client.get("/api/value").status_code == 401
        assert client.get("/api/value", headers={"Authorization": "Bearer wrong"}).status_code == 401
        assert (
            client.get("/api/value", headers={"Authorization": "Bearer secret-token"}).status_code
            == 200
        )


def test_log_redaction_hides_credentials() -> None:
    from src.evalforge.core.logging import REDACTED, redact_sensitive

    payload = {
        "api_key": "sk-live-secret",
        "nested": {"password": "hunter2", "safe": 7},
        "headers": {"authorization": "Bearer abc"},
        "items": [{"access_token": "xyz"}],
        "message": "ok",
    }
    cleaned = redact_sensitive(payload)
    assert cleaned["api_key"] == REDACTED
    assert cleaned["nested"]["password"] == REDACTED
    assert cleaned["nested"]["safe"] == 7
    assert cleaned["headers"]["authorization"] == REDACTED
    assert cleaned["items"][0]["access_token"] == REDACTED
    assert cleaned["message"] == "ok"


def test_validate_path_safety_rejects_sibling_prefix_escape(tmp_path) -> None:
    from src.evalforge.core.errors import SecurityViolationError
    from src.evalforge.core.security import validate_path_safety

    base = tmp_path / "data"
    base.mkdir()
    evil = tmp_path / "data_evil"
    evil.mkdir()

    with pytest.raises(SecurityViolationError):
        validate_path_safety(str(evil / "file.txt"), base_dir=str(base))


def test_validate_path_safety_accepts_nested_file(tmp_path) -> None:
    from src.evalforge.core.security import validate_path_safety

    base = tmp_path / "data"
    nested = base / "sub"
    nested.mkdir(parents=True)
    target = nested / "file.txt"
    target.write_text("ok")

    assert validate_path_safety(str(target), base_dir=str(base)) == str(target)


def test_validate_path_safety_rejects_base_directory_itself(tmp_path) -> None:
    from src.evalforge.core.errors import SecurityViolationError
    from src.evalforge.core.security import validate_path_safety

    with pytest.raises(SecurityViolationError):
        validate_path_safety(str(tmp_path), base_dir=str(tmp_path))
