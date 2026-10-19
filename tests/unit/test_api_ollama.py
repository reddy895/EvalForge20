"""Unit tests for Ollama status and models API routes."""

import pytest
from app.main import app
from app.providers.ollama import OllamaProvider
from app.providers.ollama_diagnostics import OllamaDiagnosticReport
from fastapi.testclient import TestClient


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def test_ollama_status_endpoint_offline(client: TestClient, monkeypatch: pytest.MonkeyPatch):
    """Test /v1/ollama/status endpoint when server is unreachable."""

    async def mock_check(base_url: str):
        return OllamaDiagnosticReport(
            is_reachable=False,
            base_url=base_url,
            installed_models=[],
            error_message="Connection refused",
            setup_instructions=["Install Ollama: curl -fsSL https://ollama.com/install.sh | sh"],
        )

    monkeypatch.setattr("app.api.routes.ollama.check_ollama_status", mock_check)

    response = client.get("/v1/ollama/status")
    assert response.status_code == 200
    data = response.json()
    assert data["is_reachable"] is False
    assert "setup_instructions" in data
    assert len(data["setup_instructions"]) > 0


def test_ollama_status_endpoint_online(client: TestClient, monkeypatch: pytest.MonkeyPatch):
    """Test /v1/ollama/status endpoint when server is online with models."""

    async def mock_check(base_url: str):
        return OllamaDiagnosticReport(
            is_reachable=True,
            base_url=base_url,
            installed_models=["qwen2.5:3b", "llama3.2:1b"],
            status_code=200,
        )

    monkeypatch.setattr("app.api.routes.ollama.check_ollama_status", mock_check)

    response = client.get("/v1/ollama/status")
    assert response.status_code == 200
    data = response.json()
    assert data["is_reachable"] is True
    assert "qwen2.5:3b" in data["installed_models"]


def test_ollama_models_endpoint(client: TestClient, monkeypatch: pytest.MonkeyPatch):
    """Test /v1/models endpoint listing detailed local models."""
    mock_models = [
        {
            "name": "qwen2.5:3b",
            "model": "qwen2.5:3b",
            "size_bytes": 1900000000,
            "parameter_size": "3B",
            "quantization_level": "Q4_K_M",
            "modified_at": "2026-10-15T12:00:00Z",
        }
    ]

    async def mock_list(self):
        return mock_models

    monkeypatch.setattr(OllamaProvider, "list_detailed_models", mock_list)

    response = client.get("/v1/models")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "qwen2.5:3b"
    assert data[0]["parameter_size"] == "3B"


def test_ollama_pull_endpoint_success(client: TestClient, monkeypatch: pytest.MonkeyPatch):
    """Test POST /v1/ollama/models/pull successfully triggers download."""
    import httpx

    class MockResponse:
        status_code = 200

        def json(self):
            return {"status": "success"}

    async def mock_post(self, url, **kwargs):
        return MockResponse()

    monkeypatch.setattr(httpx.AsyncClient, "post", mock_post)

    response = client.post("/v1/ollama/models/pull", json={"model": "qwen2.5:3b"})
    assert response.status_code == 202
    data = response.json()
    assert data["model"] == "qwen2.5:3b"
    assert data["status"] == "initiated"


def test_ollama_pull_endpoint_empty_model(client: TestClient):
    """Test POST /v1/ollama/models/pull with empty model tag raises 422."""
    response = client.post("/v1/ollama/models/pull", json={"model": "   "})
    assert response.status_code == 422


def test_ollama_pull_endpoint_connect_error(client: TestClient, monkeypatch: pytest.MonkeyPatch):
    """Test POST /v1/ollama/models/pull returns 503 when Ollama is unreachable."""
    import httpx

    async def mock_post(self, url, **kwargs):
        raise httpx.ConnectError("Connection refused")

    monkeypatch.setattr(httpx.AsyncClient, "post", mock_post)

    response = client.post("/v1/ollama/models/pull", json={"model": "qwen2.5:3b"})
    assert response.status_code == 503
