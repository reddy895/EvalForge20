"""Unit tests for cloud and custom OpenAI-compatible provider adapters."""

import httpx
import pytest
from app.domain.contracts import ProviderRequest
from app.domain.errors import NormalizedErrorCategory
from app.providers.anthropic import AnthropicProvider
from app.providers.custom_openai import CustomOpenAIProvider
from app.providers.gemini import GeminiProvider
from app.providers.nvidia import NvidiaProvider
from app.providers.openai import OpenAIProvider


@pytest.mark.asyncio
async def test_openai_missing_api_key():
    """Verify OpenAI provider returns authentication error when API key is missing."""
    provider = OpenAIProvider(api_key=None)
    provider.api_key = None  # Ensure clear override

    resp = await provider.generate(ProviderRequest(prompt="Hello"))
    assert not resp.is_success
    assert resp.error_category == NormalizedErrorCategory.AUTHENTICATION_ERROR.value
    assert "api key" in (resp.error_message or "").lower()


@pytest.mark.asyncio
async def test_openai_mock_generation(monkeypatch: pytest.MonkeyPatch):
    """Verify OpenAI chat completion parsing with mocked HTTP response."""
    provider = OpenAIProvider(api_key="mock-sk-12345", model_identifier="gpt-4o-mini")

    mock_response_data = {
        "id": "chatcmpl-123",
        "choices": [{"message": {"role": "assistant", "content": " Paris is the capital."}}],
        "usage": {"prompt_tokens": 12, "completion_tokens": 6, "total_tokens": 18},
    }

    async def mock_post(self, url, **kwargs):
        req = httpx.Request("POST", str(url))
        return httpx.Response(200, json=mock_response_data, request=req)

    monkeypatch.setattr(httpx.AsyncClient, "post", mock_post)

    resp = await provider.generate(ProviderRequest(prompt="Capital of France?"))
    assert resp.is_success
    assert resp.output_text == " Paris is the capital."
    assert resp.token_usage["total_tokens"] == 18


@pytest.mark.asyncio
async def test_anthropic_missing_api_key():
    """Verify Anthropic provider returns authentication error when unconfigured."""
    provider = AnthropicProvider(api_key=None)
    provider.api_key = None

    resp = await provider.generate(ProviderRequest(prompt="Summarize this."))
    assert not resp.is_success
    assert resp.error_category == NormalizedErrorCategory.AUTHENTICATION_ERROR.value


@pytest.mark.asyncio
async def test_anthropic_mock_messages(monkeypatch: pytest.MonkeyPatch):
    """Verify Anthropic message format extraction with mocked response."""
    provider = AnthropicProvider(
        api_key="mock-anthropic-key", model_identifier="claude-3-5-sonnet-20241022"
    )

    mock_response_data = {
        "content": [{"type": "text", "text": "Anthropic response"}],
        "usage": {"input_tokens": 15, "output_tokens": 8},
    }

    async def mock_post(self, url, **kwargs):
        req = httpx.Request("POST", str(url))
        return httpx.Response(200, json=mock_response_data, request=req)

    monkeypatch.setattr(httpx.AsyncClient, "post", mock_post)

    resp = await provider.generate(
        ProviderRequest(prompt="Explain logic gates.", system_prompt="Be concise.")
    )
    assert resp.is_success
    assert resp.output_text == "Anthropic response"
    assert resp.token_usage["prompt_tokens"] == 15


@pytest.mark.asyncio
async def test_gemini_missing_api_key():
    """Verify Google Gemini provider classifies missing credentials."""
    provider = GeminiProvider(api_key=None)
    provider.api_key = None

    resp = await provider.generate(ProviderRequest(prompt="Hello Gemini"))
    assert not resp.is_success
    assert resp.error_category == NormalizedErrorCategory.AUTHENTICATION_ERROR.value


@pytest.mark.asyncio
async def test_gemini_mock_generate_content(monkeypatch: pytest.MonkeyPatch):
    """Verify Gemini content generation parsing."""
    provider = GeminiProvider(api_key="mock-gemini-key", model_identifier="gemini-1.5-flash")

    mock_data = {
        "candidates": [
            {
                "content": {
                    "parts": [{"text": "Gemini generated text answer"}],
                    "role": "model",
                }
            }
        ],
        "usageMetadata": {
            "promptTokenCount": 8,
            "candidatesTokenCount": 5,
            "totalTokenCount": 13,
        },
    }

    async def mock_post(self, url, **kwargs):
        req = httpx.Request("POST", str(url))
        return httpx.Response(200, json=mock_data, request=req)

    monkeypatch.setattr(httpx.AsyncClient, "post", mock_post)

    resp = await provider.generate(ProviderRequest(prompt="Say hi"))
    assert resp.is_success
    assert resp.output_text == "Gemini generated text answer"
    assert resp.token_usage["total_tokens"] == 13


@pytest.mark.asyncio
async def test_nvidia_nim_mock_generation(monkeypatch: pytest.MonkeyPatch):
    """Verify NVIDIA NIM provider chat completion and token usage."""
    provider = NvidiaProvider(api_key="mock-nv-key", model_identifier="meta/llama-3.1-70b-instruct")

    mock_data = {
        "choices": [{"message": {"role": "assistant", "content": "NVIDIA NIM response"}}],
        "usage": {"prompt_tokens": 10, "completion_tokens": 4, "total_tokens": 14},
    }

    async def mock_post(self, url, **kwargs):
        req = httpx.Request("POST", str(url))
        return httpx.Response(200, json=mock_data, request=req)

    monkeypatch.setattr(httpx.AsyncClient, "post", mock_post)

    resp = await provider.generate(ProviderRequest(prompt="Hello Llama on NIM"))
    assert resp.is_success
    assert resp.output_text == "NVIDIA NIM response"
    assert resp.token_usage["prompt_tokens"] == 10


@pytest.mark.asyncio
async def test_custom_openai_provider(monkeypatch: pytest.MonkeyPatch):
    """Verify Custom OpenAI-compatible provider with arbitrary base URL."""
    provider = CustomOpenAIProvider(
        model_identifier="my-local-fine-tune",
        base_url="http://localhost:8080/v1",
        api_key="local-token",
    )

    mock_data = {
        "choices": [{"message": {"role": "assistant", "content": "Custom model output"}}],
        "usage": {"prompt_tokens": 20, "completion_tokens": 10, "total_tokens": 30},
    }

    async def mock_post(self, url, **kwargs):
        assert "localhost:8080" in str(url)
        req = httpx.Request("POST", str(url))
        return httpx.Response(200, json=mock_data, request=req)

    monkeypatch.setattr(httpx.AsyncClient, "post", mock_post)

    resp = await provider.generate(ProviderRequest(prompt="Run local model"))
    assert resp.is_success
    assert resp.output_text == "Custom model output"
