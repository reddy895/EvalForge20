"""Tests for API health, readiness, and provider separation."""

from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient
from src.evalforge.main import app


def test_health_endpoint_reports_api_ready() -> None:
    with TestClient(app) as client:
        res = client.get("/health")
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "healthy"
        assert data["api_ready"] is True
        assert data["database_connected"] is True


def test_readiness_endpoint_separates_provider_availability() -> None:
    with TestClient(app) as client:
        with patch("src.evalforge.providers.ollama.client.OllamaClient.check_health", new_callable=AsyncMock) as mock_check:
            # Simulate Ollama offline
            mock_check.return_value = False

            res = client.get("/health/ready")
            assert res.status_code == 200
            data = res.json()
            assert data["status"] == "ready"
            assert data["api_ready"] is True
            assert data["providers_online"]["ollama"] is False
            assert data["providers_online"]["mock"] is True


def test_liveness_endpoint() -> None:
    with TestClient(app) as client:
        res = client.get("/health/live")
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "alive"
        assert "timestamp" in data
