"""Unit tests for unified model catalog service, pricing lookup, and API endpoints."""

import httpx
import pytest
from app.catalog.models import CatalogModel
from app.catalog.service import ModelCatalogService


@pytest.mark.asyncio
async def test_catalog_retrieves_verified_pricing():
    """Verify official pricing metadata is correctly attached to catalog models."""
    service = ModelCatalogService()
    gpt4o = await service.get_model("openai", "gpt-4o")
    assert gpt4o is not None
    assert gpt4o.pricing is not None
    assert gpt4o.pricing.input_cost_per_m == 2.50
    assert gpt4o.pricing.output_cost_per_m == 10.00
    assert gpt4o.pricing.cached_input_cost_per_m == 1.25
    assert gpt4o.context_window == 128000
    assert "https://developers.openai.com" in (gpt4o.pricing.source_url or "")

    claude = await service.get_model("anthropic", "claude-3-5-sonnet-20241022")
    assert claude is not None
    assert claude.pricing is not None
    assert claude.pricing.input_cost_per_m == 3.00
    assert claude.pricing.output_cost_per_m == 15.00


@pytest.mark.asyncio
async def test_catalog_custom_model_registration():
    """Verify registering a custom model dynamically in catalog."""
    service = ModelCatalogService()
    custom = CatalogModel(
        id="custom/my-special-llm",
        model_identifier="my-special-llm",
        provider="custom_openai",
        display_name="My Special LLM",
        is_local=False,
        is_available=True,
    )
    service.register_custom_model(custom)

    found = await service.get_model("custom_openai", "my-special-llm")
    assert found is not None
    assert found.display_name == "My Special LLM"


@pytest.mark.asyncio
async def test_catalog_filtering():
    """Verify filtering catalog by provider, search query, and locality."""
    service = ModelCatalogService()

    # Search filter
    search_results = await service.get_all_models(search="sonnet")
    assert any("claude-3-5-sonnet" in m.model_identifier for m in search_results)
    assert all(
        "claude" in m.model_identifier or "sonnet" in m.display_name.lower() for m in search_results
    )

    # Provider filter
    openai_models = await service.get_all_models(provider="openai")
    assert len(openai_models) >= 2
    assert all(m.provider == "openai" for m in openai_models)

    # Local filter
    local_models = await service.get_all_models(is_local=True)
    assert all(m.is_local for m in local_models)


@pytest.mark.asyncio
async def test_catalog_ollama_discovery_graceful_offline(monkeypatch: pytest.MonkeyPatch):
    """Verify that when Ollama is offline, catalog still returns other models gracefully."""

    async def mock_offline_status(*args, **kwargs):
        from app.providers.ollama_diagnostics import OllamaDiagnosticReport

        return OllamaDiagnosticReport(
            is_reachable=False,
            version=None,
            latency_ms=0.0,
            models_count=0,
            models=[],
            error="Connection refused",
        )

    monkeypatch.setattr("app.catalog.service.check_ollama_status", mock_offline_status)

    service = ModelCatalogService()
    models = await service.get_all_models()
    assert len(models) > 0

    # Ollama models should be marked unavailable when offline
    ollama_models = [m for m in models if m.provider == "ollama"]
    for om in ollama_models:
        assert not om.is_available


@pytest.mark.asyncio
async def test_catalog_api_routes():
    """Verify catalog FastAPI endpoints."""
    from app.main import app

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://testserver"
    ) as client:
        # GET /v1/catalog/models
        resp = await client.get("/v1/catalog/models?provider=openai")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) >= 2

        # GET /v1/catalog/providers
        p_resp = await client.get("/v1/catalog/providers")
        assert p_resp.status_code == 200
        providers_data = p_resp.json()
        assert any(p["provider"] == "ollama" for p in providers_data)
        assert any(p["provider"] == "openai" for p in providers_data)
