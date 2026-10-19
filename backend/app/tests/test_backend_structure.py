"""Tests validating backend modules and entrypoint integrity."""

from fastapi.testclient import TestClient

from app.config import get_settings
from app.evaluators.registry import registry
from app.main import app
from app.providers.registry import provider_registry


def test_backend_app_instance():
    """Verify backend application exports valid FastAPI instance."""
    client = TestClient(app)
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_backend_submodules_importable():
    """Verify core, schemas, services, providers, evaluators, db are imported cleanly."""
    settings = get_settings()
    assert settings is not None
    assert "exact_match" in registry.list_metric_ids()
    assert "mock" in provider_registry.list_providers()
