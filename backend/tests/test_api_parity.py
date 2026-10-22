"""Integration tests verifying route parity across /api/ and /api/v1/ endpoints."""

from starlette.testclient import TestClient
from src.evalforge.main import app

def test_api_route_parity() -> None:
    with TestClient(app) as client:
        # Health
        assert client.get("/health").status_code == 200
        assert client.get("/api/health").status_code == 200

        # Providers
        assert client.get("/api/providers").status_code == 200
        assert client.get("/api/v1/providers").status_code == 200

        # Analytics
        assert client.get("/api/analytics/overview").status_code == 200
        assert client.get("/api/v1/analytics/overview").status_code == 200
        assert client.get("/api/analytics/commits").status_code == 200
