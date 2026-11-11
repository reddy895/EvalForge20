"""Tests for the provider connection diagnostics endpoint."""

from fastapi.testclient import TestClient

from src.evalforge.main import app


def test_mock_provider_connection_test_succeeds() -> None:
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/providers/mock/test",
            json={"model_id": "mock-llama-3.1-8b", "prompt": "Say OK"},
        )
        assert response.status_code == 200
        payload = response.json()
        assert payload["provider"] == "mock"
        assert payload["configured"] is True
        assert payload["status"] == "connected"
        assert payload["model_identifier"] == "mock-llama-3.1-8b"
        assert payload["latency_ms"] >= 0
        assert payload["response_sample"]


def test_unconfigured_cloud_provider_reports_missing_credentials() -> None:
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/providers/openai/test",
            json={"model_id": "gpt-4o-mini"},
        )
        assert response.status_code == 200
        payload = response.json()
        assert payload["provider"] == "openai"
        assert payload["configured"] is False
        assert payload["status"] == "not_configured"
        assert payload["error_message"]


def test_unknown_provider_returns_structured_provider_error() -> None:
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/providers/does-not-exist/test",
            json={"model_id": "whatever"},
        )
        assert response.status_code >= 400
        assert "error" in response.json()


def test_empty_model_identifier_is_rejected() -> None:
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/providers/mock/test",
            json={"model_id": ""},
        )
        assert response.status_code == 422
