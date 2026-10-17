"""Unit tests for /health and /ready system endpoints."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from app.main import app
from app.providers.ollama_diagnostics import OllamaDiagnosticReport
from app.storage.database import get_db
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    return TestClient(app)


def test_health_endpoint_returns_ok(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "version" in data
    assert "environment" in data


def test_readiness_endpoint_with_offline_ollama(client):
    with patch(
        "app.api.routes.health.check_ollama_status",
        new=AsyncMock(
            return_value=OllamaDiagnosticReport(
                is_reachable=False,
                base_url="http://localhost:11434",
                installed_models=[],
                status_code=None,
                error_message="Connection refused",
                setup_instructions=["Install Ollama"],
            )
        ),
    ):
        response = client.get("/ready")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ready"
        assert data["database"] == "connected"
        assert "providers_status" in data
        assert data["providers_status"]["ollama"] == "offline"
        assert data["providers_status"]["mock"] == "online"
        assert data["providers_status"]["sqlite"] == "connected"


def test_readiness_endpoint_with_online_ollama(client):
    with patch(
        "app.api.routes.health.check_ollama_status",
        new=AsyncMock(
            return_value=OllamaDiagnosticReport(
                is_reachable=True,
                base_url="http://localhost:11434",
                installed_models=["qwen2.5:3b", "llama3.1:8b"],
                status_code=200,
                error_message=None,
                setup_instructions=[],
            )
        ),
    ):
        response = client.get("/ready")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ready"
        assert data["providers_status"]["ollama"] == "online"


def test_readiness_endpoint_db_failure_returns_503(client):
    mock_db = MagicMock()
    mock_db.execute.side_effect = Exception("Disk I/O error or SQLite lock timeout")

    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        with patch("app.api.routes.health.check_ollama_status", new=AsyncMock()):
            response = client.get("/ready")
            assert response.status_code == 503
            assert "Database connection error" in response.json()["detail"]
    finally:
        app.dependency_overrides.pop(get_db, None)
