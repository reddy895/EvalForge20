"""Platform End-to-End Regression Tests.

Validates backend startup health contract, decoupling of API readiness from provider reachability,
and robust handling of evaluation endpoints under varied provider states.
"""

import pytest
from starlette.testclient import TestClient
from src.evalforge.main import app


def test_api_readiness_endpoint() -> None:
    """GET /health must return HTTP 200 indicating FastAPI application is ready."""
    with TestClient(app) as client:
        res = client.get("/health")
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "healthy"
        assert "EvalForge20" in data["app"]
        assert data["api_ready"] is True
        assert data["database_connected"] is True


def test_ollama_provider_health_decoupling() -> None:
    """GET /health/ready reports API server readiness separately from external provider reachability."""
    with TestClient(app) as client:
        res = client.get("/health/ready")
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "ready"
        assert data["api_ready"] is True
        assert "providers_online" in data
        assert "ollama" in data["providers_online"]


def test_provider_models_endpoint_contract() -> None:
    """GET /api/v1/models returns registered models and indicates readiness."""
    with TestClient(app) as client:
        res = client.get("/api/v1/models")
        assert res.status_code == 200
        data = res.json()
        assert "models" in data
        models = data["models"]
        assert isinstance(models, list)
        assert len(models) > 0
        for m in models:
            assert "id" in m
            assert "name" in m
            assert "provider" in m
