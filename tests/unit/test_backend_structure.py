"""Unit tests for the backend application package and directory layout."""

from app.config import get_settings
from app.evaluators.registry import registry
from app.main import app
from app.providers.registry import provider_registry
from fastapi.testclient import TestClient


def test_backend_app_routes():
    """Verify that root FastAPI application has all expected endpoints mounted."""
    client = TestClient(app)
    health_resp = client.get("/health")
    assert health_resp.status_code == 200
    assert health_resp.json()["status"] == "ok"

    ready_resp = client.get("/ready")
    assert ready_resp.status_code == 200

    models_resp = client.get("/v1/models")
    assert models_resp.status_code == 200

    ollama_resp = client.get("/v1/ollama/status")
    assert ollama_resp.status_code == 200


def test_backend_registries_loaded():
    """Verify core evaluators and providers registries are populated."""
    settings = get_settings()
    assert settings.ollama_base_url is not None
    assert "exact_match" in registry.list_metric_ids()
    assert "mock" in provider_registry.list_providers()
