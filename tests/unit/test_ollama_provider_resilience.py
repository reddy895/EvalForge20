"""Unit tests for OllamaProvider resilience, missing model guidance, and timeout handling."""

from unittest.mock import AsyncMock, patch

import httpx
import pytest
from app.domain.contracts import ProviderRequest
from app.domain.errors import NormalizedErrorCategory
from app.providers.ollama import OllamaProvider


@pytest.mark.asyncio
async def test_ollama_generate_success():
    provider = OllamaProvider(model_identifier="qwen2.5:3b", base_url="http://localhost:11434")

    mock_resp = httpx.Response(
        status_code=200,
        json={
            "model": "qwen2.5:3b",
            "response": "Paris is the capital of France.",
            "prompt_eval_count": 14,
            "eval_count": 8,
            "done": True,
        },
        request=httpx.Request("POST", "http://localhost:11434/api/generate"),
    )

    with patch("httpx.AsyncClient.post", new=AsyncMock(return_value=mock_resp)):
        req = ProviderRequest(prompt="What is the capital of France?")
        res = await provider.generate(req)

        assert res.is_success is True
        assert res.output_text == "Paris is the capital of France."
        assert res.token_usage == {
            "prompt_tokens": 14,
            "completion_tokens": 8,
            "total_tokens": 22,
        }
        assert res.error_category is None


@pytest.mark.asyncio
async def test_ollama_generate_missing_model_404():
    provider = OllamaProvider(model_identifier="llama3.3:70b", base_url="http://localhost:11434")

    mock_resp = httpx.Response(
        status_code=404,
        json={"error": "model 'llama3.3:70b' not found, try pulling it first"},
        request=httpx.Request("POST", "http://localhost:11434/api/generate"),
    )

    with patch("httpx.AsyncClient.post", new=AsyncMock(return_value=mock_resp)):
        req = ProviderRequest(prompt="Test prompt")
        res = await provider.generate(req)

        assert res.is_success is False
        assert res.output_text is None
        assert res.error_category == NormalizedErrorCategory.PROVIDER_UNAVAILABLE.value
        assert "ollama pull llama3.3:70b" in (res.error_message or "")


@pytest.mark.asyncio
async def test_ollama_generate_daemon_offline_connect_error():
    provider = OllamaProvider(model_identifier="qwen2.5:3b", base_url="http://localhost:11434")

    with patch(
        "httpx.AsyncClient.post",
        side_effect=httpx.ConnectError("Connection refused to 127.0.0.1:11434"),
    ):
        req = ProviderRequest(prompt="Test prompt")
        res = await provider.generate(req)

        assert res.is_success is False
        assert res.output_text is None
        assert res.error_category == NormalizedErrorCategory.PROVIDER_UNAVAILABLE.value
        assert "ollama serve" in (res.error_message or "").lower()


@pytest.mark.asyncio
async def test_ollama_generate_timeout():
    provider = OllamaProvider(
        model_identifier="qwen2.5:3b", base_url="http://localhost:11434", timeout_seconds=2.0
    )

    with patch(
        "httpx.AsyncClient.post",
        side_effect=httpx.TimeoutException("Request timed out after 2.0s"),
    ):
        req = ProviderRequest(prompt="Test prompt")
        res = await provider.generate(req)

        assert res.is_success is False
        assert res.output_text is None
        assert res.error_category == NormalizedErrorCategory.TIMEOUT.value
        assert "timed out after 2.0s" in (res.error_message or "")


@pytest.mark.asyncio
async def test_ollama_list_detailed_models():
    provider = OllamaProvider(base_url="http://localhost:11434")

    mock_resp = httpx.Response(
        status_code=200,
        json={
            "models": [
                {
                    "name": "qwen2.5:3b",
                    "model": "qwen2.5:3b",
                    "modified_at": "2026-03-29T10:00:00Z",
                    "size": 1928000000,
                    "digest": "abc123hash",
                    "details": {
                        "parent_model": "",
                        "format": "gguf",
                        "family": "qwen2",
                        "families": ["qwen2"],
                        "parameter_size": "3.1B",
                        "quantization_level": "Q4_K_M",
                    },
                }
            ]
        },
        request=httpx.Request("GET", "http://localhost:11434/api/tags"),
    )

    with patch("httpx.AsyncClient.get", new=AsyncMock(return_value=mock_resp)):
        models = await provider.list_detailed_models()
        assert len(models) == 1
        m = models[0]
        assert m.name == "qwen2.5:3b"
        assert m.parameter_size == "3.1B"
        assert m.quantization_level == "Q4_K_M"
        assert m.family == "qwen2"
        assert m.size == 1928000000
        assert m.digest == "abc123hash"
