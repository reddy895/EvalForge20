"""Tests for Ollama connectivity reporting and model pull endpoints."""

from backend.app.main import app
from fastapi.testclient import TestClient

client = TestClient(app)


def test_ollama_status_offline():
    """Verify endpoint gracefully handles offline daemon without throwing 500."""
    resp = client.get("/v1/ollama/status")
    assert resp.status_code == 200
    data = resp.json()
    assert "is_reachable" in data
    assert "status_label" in data
    assert data["status_label"] in ("online", "no_models_installed", "offline")
    assert "setup_instructions" in data


def test_ollama_pull_validation():
    """Verify empty model tag validation."""
    resp = client.post("/v1/ollama/pull", json={"model": "   "})
    assert resp.status_code == 400
