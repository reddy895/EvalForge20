"""Tests validating backend modules and entrypoint integrity."""

from backend.app.core.config import get_settings
from backend.app.main import app
from fastapi.testclient import TestClient


def test_backend_app_instance():
    """Verify backend application exports valid FastAPI instance."""
    client = TestClient(app)
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_backend_submodules_importable():
    """Verify core configuration and routes are mounted cleanly."""
    settings = get_settings()
    assert settings is not None
    assert settings.ollama_base_url is not None
