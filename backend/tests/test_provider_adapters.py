"""Tests for the multi-provider registry, adapter initialization, capability reporting, and error mapping."""

import pytest
from starlette.testclient import TestClient

from src.evalforge.core.errors import ProviderError
from src.evalforge.main import app
from src.evalforge.providers.adapters import (
    AnthropicProvider,
)
from src.evalforge.providers.base import BaseProvider
from src.evalforge.providers.openai_compatible import OpenAICompatibleProvider
from src.evalforge.providers.registry import get_provider_registry
from src.evalforge.providers.schemas import InferenceRequest


def test_registry_contains_all_target_providers() -> None:
    registry = get_provider_registry()
    providers = registry.list_providers()

    expected_providers = {
        "ollama",
        "mock",
        "openai",
        "anthropic",
        "gemini",
        "groq",
        "mistral",
        "cohere",
        "together",
        "fireworks",
        "deepseek",
        "huggingface",
        "azure",
        "bedrock",
        "openai_compatible",
    }

    assert expected_providers.issubset(set(providers.keys()))
    assert len(providers) >= 15


def test_all_adapters_subclass_base_provider() -> None:
    registry = get_provider_registry()
    for name, provider in registry.list_providers().items():
        assert isinstance(provider, BaseProvider), f"Provider {name} must inherit from BaseProvider"
        assert provider.name == name
        assert provider.display_name


@pytest.mark.asyncio
async def test_provider_status_categorization() -> None:
    registry = get_provider_registry()
    status_list = await registry.list_details()

    statuses = {p.implementation_status for p in status_list}
    assert "implemented_and_tested" in statuses

    # Mock and Ollama should be implemented and tested
    mock_info = next(p for p in status_list if p.name == "mock")
    assert mock_info.implementation_status == "implemented_and_tested"
    assert mock_info.provider_type == "local"

    # Cloud adapters should require API keys and report setup instructions
    openai_info = next(p for p in status_list if p.name == "openai")
    assert "OPENAI_API_KEY" in (openai_info.setup_instructions or "")


@pytest.mark.asyncio
async def test_unconfigured_cloud_provider_raises_meaningful_error() -> None:
    adapter = AnthropicProvider(api_key=None)
    req = InferenceRequest(model="claude-3-5-sonnet", prompt="Hello")
    with pytest.raises(ProviderError) as exc_info:
        await adapter.generate(req)
    assert "not configured" in str(exc_info.value).lower() or "anthropic" in str(exc_info.value).lower()


def test_openai_compatible_adapter_custom_url() -> None:
    adapter = OpenAICompatibleProvider(
        name="custom_vllm",
        display_name="vLLM Inference",
        base_url="http://localhost:8000/v1",
        api_key="sk-test",
    )
    assert adapter.base_url == "http://localhost:8000/v1"
    assert adapter.name == "custom_vllm"
    assert adapter.is_configured is True


def test_api_providers_endpoints() -> None:
    with TestClient(app) as client:
        # Test basic list
        resp = client.get("/api/providers")
        assert resp.status_code == 200
        data = resp.json()
        assert "providers" in data
        assert len(data["providers"]) >= 15

        # Test details list
        detail_resp = client.get("/api/providers/details")
        assert detail_resp.status_code == 200
        detail_data = detail_resp.json()
        assert "providers" in detail_data
        assert detail_data["total"] >= 15
        assert any(p["name"] == "ollama" for p in detail_data["providers"])
