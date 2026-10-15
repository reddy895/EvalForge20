"""Unit tests for model providers, error classification, and Ollama adapter."""

import httpx
import pytest
from app.domain.contracts import ProviderRequest
from app.domain.errors import NormalizedErrorCategory, ProviderError
from app.providers.mock import MockProvider
from app.providers.ollama import OllamaProvider
from app.providers.registry import provider_registry


@pytest.mark.asyncio
async def test_mock_provider_canned_responses():
    """Verify mock provider returns canned response when matched."""
    provider = MockProvider(
        canned_responses={"capital of France": "Paris", "6 multiplied by 7": "42"},
        default_response="Unknown prompt",
        simulated_tokens={"prompt_tokens": 5, "completion_tokens": 2, "total_tokens": 7},
    )

    req = ProviderRequest(prompt="What is the capital of France?")
    resp = await provider.generate(req)

    assert resp.is_success
    assert resp.output_text == "Paris"
    assert resp.latency_ms >= 0.0
    assert resp.token_usage == {"prompt_tokens": 5, "completion_tokens": 2, "total_tokens": 7}


@pytest.mark.asyncio
async def test_mock_provider_fallback_response():
    """Verify mock provider returns default response when no canned match is found."""
    provider = MockProvider(default_response="Default answer")
    req = ProviderRequest(prompt="Unmatched query")
    resp = await provider.generate(req)

    assert resp.is_success
    assert resp.output_text == "Default answer"


@pytest.mark.asyncio
async def test_mock_provider_simulated_failures():
    """Verify simulated provider errors are mapped to normalized error categories."""
    provider = MockProvider(
        fail_on_prompts={
            "trigger_timeout": NormalizedErrorCategory.TIMEOUT,
            "trigger_rate_limit": NormalizedErrorCategory.RATE_LIMIT,
            "trigger_conn_error": ConnectionRefusedError("Connection refused by host"),
        }
    )

    # Test Timeout
    resp_timeout = await provider.generate(ProviderRequest(prompt="trigger_timeout now"))
    assert not resp_timeout.is_success
    assert resp_timeout.error_category == NormalizedErrorCategory.TIMEOUT.value

    # Test Rate Limit
    resp_rate = await provider.generate(ProviderRequest(prompt="trigger_rate_limit now"))
    assert not resp_rate.is_success
    assert resp_rate.error_category == NormalizedErrorCategory.RATE_LIMIT.value

    # Test Connection Refused
    resp_conn = await provider.generate(ProviderRequest(prompt="trigger_conn_error now"))
    assert not resp_conn.is_success
    assert resp_conn.error_category == NormalizedErrorCategory.PROVIDER_UNAVAILABLE.value


def test_provider_registry():
    """Verify provider discovery and lookup."""
    mock = provider_registry.get("mock")
    assert isinstance(mock, MockProvider)

    ollama = provider_registry.get("ollama")
    assert isinstance(ollama, OllamaProvider)

    with pytest.raises(ProviderError) as exc_info:
        provider_registry.get("unregistered_provider")
    assert "Unknown provider" in str(exc_info.value)


@pytest.mark.asyncio
async def test_ollama_provider_mocked_http(monkeypatch: pytest.MonkeyPatch):
    """Verify Ollama provider against mocked HTTP responses without requiring running Ollama."""
    provider = OllamaProvider(model_identifier="qwen2.5:3b", base_url="http://mock-ollama:11434")

    # Mock health check
    async def mock_health_get(self, url, **kwargs):
        req = httpx.Request("GET", str(url))
        return httpx.Response(
            200, request=req, json={"models": [{"name": "qwen2.5:3b"}, {"name": "llama3:8b"}]}
        )

    monkeypatch.setattr(httpx.AsyncClient, "get", mock_health_get)

    is_healthy = await provider.health_check()
    assert is_healthy is True

    models = await provider.list_models()
    assert "qwen2.5:3b" in models
    assert "llama3:8b" in models

    # Mock generate call
    async def mock_generate_post(self, url, **kwargs):
        payload = kwargs.get("json", {})
        assert payload.get("model") == "qwen2.5:3b"
        req = httpx.Request("POST", str(url))
        return httpx.Response(
            200,
            request=req,
            json={
                "response": "Rome is the capital of Italy.",
                "eval_count": 8,
                "prompt_eval_count": 12,
                "done": True,
            },
        )

    monkeypatch.setattr(httpx.AsyncClient, "post", mock_generate_post)

    req = ProviderRequest(prompt="What is the capital of Italy?")
    resp = await provider.generate(req)

    assert resp.is_success
    assert resp.output_text == "Rome is the capital of Italy."
    assert resp.token_usage == {"prompt_tokens": 12, "completion_tokens": 8, "total_tokens": 20}


@pytest.mark.asyncio
async def test_ollama_provider_connection_failure(monkeypatch: pytest.MonkeyPatch):
    """Verify Ollama provider gracefully classifies connection errors."""
    provider = OllamaProvider(base_url="http://nonexistent-host:11434")

    async def mock_failed_post(self, url, **kwargs):
        raise httpx.ConnectError("Connection refused by nonexistent-host")

    monkeypatch.setattr(httpx.AsyncClient, "post", mock_failed_post)

    resp = await provider.generate(ProviderRequest(prompt="test connection"))
    assert not resp.is_success
    assert resp.error_category == NormalizedErrorCategory.PROVIDER_UNAVAILABLE.value
    assert "Cannot connect to ollama" in (resp.error_message or "")
