"""Tests for Ollama provider integration, discovery, and connection testing."""

from unittest.mock import AsyncMock, patch

import pytest

from src.evalforge.providers.ollama import OllamaProvider, get_ollama_provider
from src.evalforge.providers.schemas import InferenceResponse, TokenUsage


@pytest.mark.asyncio
async def test_ollama_provider_initialization():
    provider = get_ollama_provider()
    assert provider.name == "ollama"
    assert provider.provider_type == "local"
    assert provider.is_configured is True


@pytest.mark.asyncio
async def test_ollama_provider_health_check_healthy():
    provider = OllamaProvider()
    with patch.object(provider.client, "check_health", new_callable=AsyncMock) as mock_health:
        mock_health.return_value = True
        is_healthy = await provider.health_check()
        assert is_healthy is True


@pytest.mark.asyncio
async def test_ollama_provider_list_models():
    provider = OllamaProvider()
    mock_tags = {
        "models": [
            {
                "name": "qwen2.5:3b",
                "size": 1929912432,
                "details": {
                    "parameter_size": "3.1B",
                    "quantization_level": "Q4_K_M",
                    "family": "qwen2",
                    "context_length": 32768,
                },
                "capabilities": ["completion", "tools"],
            }
        ]
    }
    with patch.object(provider.client, "list_tags", new_callable=AsyncMock) as mock_list:
        mock_list.return_value = mock_tags
        models = await provider.list_models()
        assert len(models) == 1
        assert models[0].name == "qwen2.5:3b"
        assert models[0].family == "qwen2"
        assert models[0].supports_tools is True
        assert models[0].is_local is True


@pytest.mark.asyncio
async def test_ollama_provider_test_connection():
    provider = OllamaProvider()
    mock_response = InferenceResponse(
        text="OK",
        model="qwen2.5:3b",
        provider="ollama",
        usage=TokenUsage(prompt_tokens=4, completion_tokens=1, total_tokens=5),
        latency_ms=45.0,
    )
    with patch.object(provider, "generate", new_callable=AsyncMock) as mock_gen:
        mock_gen.return_value = mock_response
        result = await provider.test_connection("qwen2.5:3b")
        assert result["status"] == "connected"
        assert result["model_identifier"] == "qwen2.5:3b"
        assert result["response_sample"] == "OK"
