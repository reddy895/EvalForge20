"""Tests for model catalog, dynamic discovery, search, filtering, and model metadata."""

import pytest
from starlette.testclient import TestClient

from src.evalforge.main import app
from src.evalforge.services.model_service import (
    VERIFIED_CATALOG_MODELS,
    get_model_service,
)


def test_model_service_catalog_completeness() -> None:
    models = VERIFIED_CATALOG_MODELS

    # Verify minimum catalog size and representation across families
    assert len(models) >= 10

    # Verify essential model families are present
    model_ids = [m.id for m in models]
    assert any("qwen" in mid for mid in model_ids)
    assert any("llama" in mid for mid in model_ids)
    assert any("deepseek" in mid for mid in model_ids)
    assert any("mistral" in mid for mid in model_ids)
    assert any("claude" in mid for mid in model_ids)
    assert any("gpt" in mid for mid in model_ids)

    # Check model specifications
    for model in models:
        assert model.name
        assert model.provider
        assert model.context_window > 0
        if not model.id.startswith("mock-"):
            assert model.benchmarks
        assert model.recommended_tasks
        if model.is_local:
            assert model.hardware.min_ram_gb > 0
            assert model.pricing.input_cost_per_m == 0.0
            assert model.pricing.is_free_local is True


@pytest.mark.asyncio
async def test_model_service_filtering_and_search() -> None:
    service = get_model_service()

    # Search by text query
    qwen_results, total = await service.filter_models(query="qwen")
    assert total > 0
    assert all("qwen" in m.id.lower() or "qwen" in m.name.lower() for m in qwen_results)

    # Filter local only
    local_models, _ = await service.filter_models(is_local=True)
    assert all(m.is_local for m in local_models)

    # Filter cloud only
    cloud_models, _ = await service.filter_models(is_local=False)
    assert all(not m.is_local for m in cloud_models)

    # Filter by task
    coding_models, _ = await service.filter_models(task="coding")
    assert len(coding_models) > 0
    assert all(any("coding" in t.lower() for t in m.recommended_tasks) for m in coding_models)


@pytest.mark.asyncio
async def test_dynamic_discovery_fallback_when_offline() -> None:
    service = get_model_service()
    # When Ollama is offline or uninstalled, dynamic discovery safely returns catalog
    discovered = await service.get_all_models()
    assert len(discovered) >= 10
    assert any(m.id == "qwen-2.5-7b-instruct" for m in discovered)


def test_api_models_endpoint() -> None:
    with TestClient(app) as client:
        # Test standard /api/models
        response = client.get("/api/models")
        assert response.status_code == 200
        data = response.json()
        assert "models" in data
        assert "total" in data
        assert data["total"] >= 10

        # Test model details
        detail_resp = client.get("/api/models/qwen-2.5-7b-instruct")
        assert detail_resp.status_code == 200
        detail_data = detail_resp.json()
        assert detail_data["id"] == "qwen-2.5-7b-instruct"
        assert detail_data["is_local"] is True
        assert detail_data["hardware"]["min_ram_gb"] >= 8

        # Test refresh endpoint
        refresh_resp = client.post("/api/models/refresh")
        assert refresh_resp.status_code == 200
        refresh_data = refresh_resp.json()
        assert refresh_data["success"] is True
        assert refresh_data["total_models"] >= 10
        assert "refreshed_at" in refresh_data
