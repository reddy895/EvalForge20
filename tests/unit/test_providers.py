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


@pytest.mark.asyncio
async def test_ollama_list_detailed_models(monkeypatch: pytest.MonkeyPatch):
    """Verify detailed model inspection with quantization and parameter counts."""
    provider = OllamaProvider(base_url="http://mock-ollama:11434")

    sample_tags = {
        "models": [
            {
                "name": "qwen2.5:3b",
                "size": 1920000000,
                "modified_at": "2026-01-01T00:00:00Z",
                "details": {
                    "family": "qwen2",
                    "parameter_size": "3.1B",
                    "quantization_level": "Q4_K_M",
                },
            }
        ]
    }

    async def mock_tags(self, url, **kwargs):
        return httpx.Response(status_code=200, json=sample_tags, request=httpx.Request("GET", url))

    monkeypatch.setattr(httpx.AsyncClient, "get", mock_tags)

    detailed = await provider.list_detailed_models()
    assert len(detailed) == 1
    assert detailed[0].name == "qwen2.5:3b"
    assert detailed[0].parameter_size == "3.1B"
    assert detailed[0].quantization_level == "Q4_K_M"
    assert detailed[0].size_bytes == 1920000000

    names = await provider.list_models()
    assert names == ["qwen2.5:3b"]


@pytest.mark.asyncio
async def test_ollama_missing_model_404(monkeypatch: pytest.MonkeyPatch):
    """Verify 404 response provides setup instructions to pull the model."""
    provider = OllamaProvider(
        model_identifier="missing-model:latest", base_url="http://mock-ollama:11434"
    )

    async def mock_404(self, url, **kwargs):
        return httpx.Response(
            status_code=404,
            json={"error": "model 'missing-model:latest' not found"},
            request=httpx.Request("POST", url),
        )

    monkeypatch.setattr(httpx.AsyncClient, "post", mock_404)

    resp = await provider.generate(ProviderRequest(prompt="Hello"))
    assert not resp.is_success
    assert "ollama pull missing-model:latest" in (resp.error_message or "")


@pytest.mark.asyncio
async def test_ollama_inference_options_payload(monkeypatch: pytest.MonkeyPatch):
    """Verify context length and temperature options are correctly serialized."""
    provider = OllamaProvider(model_identifier="qwen2.5:3b", base_url="http://mock-ollama:11434")

    captured_payload = {}

    async def mock_generate(self, url, **kwargs):
        nonlocal captured_payload
        captured_payload = kwargs.get("json", {})
        return httpx.Response(
            status_code=200,
            json={"response": "Mock reply", "prompt_eval_count": 5, "eval_count": 10},
            request=httpx.Request("POST", url),
        )

    monkeypatch.setattr(httpx.AsyncClient, "post", mock_generate)

    req = ProviderRequest(
        prompt="Tell a story",
        temperature=0.2,
        max_tokens=256,
        extra_params={"context_length": 8192, "top_k": 40, "seed": 42},
    )
    resp = await provider.generate(req)
    assert resp.is_success
    opts = captured_payload.get("options", {})
    assert opts.get("temperature") == 0.2
    assert opts.get("num_ctx") == 8192
    assert opts.get("top_k") == 40
    assert opts.get("seed") == 42
