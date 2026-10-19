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


def test_ollama_models_endpoint():
    """Verify /v1/ollama/models returns installed models status."""
    resp = client.get("/v1/ollama/models")
    assert resp.status_code == 200
    data = resp.json()
    assert "installed_models" in data
    assert "models_count" in data


def test_ollama_generate_mock_model():
    """Verify inference generation endpoint with deterministic mock target."""
    resp = client.post(
        "/v1/ollama/generate",
        json={
            "model": "mock-model-v1",
            "prompt": "def reverse_string(s: str) -> str:",
            "temperature": 0.0,
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["model"] == "mock-model-v1"
    assert "return s[::-1]" in data["output"]
    assert data["latency_ms"] > 0
    assert data["total_tokens"] > 0
    assert data["is_success"] is True


def test_ollama_generate_offline_unreachable_error():
    """Verify that targeting an uninstalled model when Ollama daemon is down returns 503."""
    resp = client.post(
        "/v1/ollama/generate",
        json={
            "model": "nonexistent-local-model:7b",
            "prompt": "Hello world",
        },
    )
    # Since Ollama daemon is offline in test env, it gracefully reports 503 Service Unavailable
    assert resp.status_code in (503, 404)

