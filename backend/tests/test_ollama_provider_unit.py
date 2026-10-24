"""Unit tests for OllamaProvider — telemetry extraction, token-per-second computation, and model normalization."""

from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.evalforge.providers.ollama.provider import OllamaProvider
from src.evalforge.providers.schemas import InferenceRequest


def _make_ollama_response(**overrides: Any) -> dict[str, Any]:
    """Produce a realistic Ollama generate/chat API response dict."""
    base = {
        "model": "qwen2.5:1.5b",
        "message": {"role": "assistant", "content": "Paris."},
        "response": "Paris.",
        "done": True,
        "prompt_eval_count": 15,
        "eval_count": 3,
        "total_duration": 500_000_000,       # 500 ms in ns
        "load_duration": 100_000_000,         # 100 ms in ns
        "prompt_eval_duration": 50_000_000,   # 50 ms in ns
        "eval_duration": 200_000_000,         # 200 ms in ns
    }
    base.update(overrides)
    return base


class TestOllamaProviderTelemetry:
    """Tests for nanosecond duration extraction and tokens-per-second calculation."""

    @pytest.fixture()
    def mock_client(self) -> MagicMock:
        client = MagicMock()
        client.chat = AsyncMock(return_value=_make_ollama_response())
        client.generate = AsyncMock(return_value=_make_ollama_response())
        return client

    @pytest.fixture()
    def provider(self, mock_client: MagicMock) -> OllamaProvider:
        return OllamaProvider(client=mock_client)

    @pytest.mark.asyncio
    async def test_chat_response_latency_derived_from_total_duration_ns(
        self, provider: OllamaProvider, mock_client: MagicMock
    ) -> None:
        request = InferenceRequest(
            model="qwen2.5:1.5b",
            prompt="What is the capital of France?",
            messages=[{"role": "user", "content": "What is the capital of France?"}],
        )
        resp = await provider.generate(request)
        # 500_000_000 ns == 500 ms
        assert resp.latency_ms == pytest.approx(500.0, abs=1.0)

    @pytest.mark.asyncio
    async def test_tokens_per_second_computed_correctly(
        self, provider: OllamaProvider, mock_client: MagicMock
    ) -> None:
        # eval_count=3, eval_duration=200_000_000 ns => 3 / 0.2s = 15.0 tok/s
        request = InferenceRequest(
            model="qwen2.5:1.5b",
            prompt="Capitale de France?",
            messages=[{"role": "user", "content": "Capitale de France?"}],
        )
        resp = await provider.generate(request)
        tps = resp.raw_metadata.get("tokens_per_second")
        assert tps is not None
        assert tps == pytest.approx(15.0, abs=0.5)

    @pytest.mark.asyncio
    async def test_load_duration_stored_in_ms(
        self, provider: OllamaProvider, mock_client: MagicMock
    ) -> None:
        request = InferenceRequest(model="qwen2.5:1.5b", prompt="Hi")
        mock_client.generate = AsyncMock(return_value=_make_ollama_response())
        resp = await provider.generate(request)
        load_ms = resp.raw_metadata.get("load_duration_ms")
        # 100_000_000 ns == 100 ms
        assert load_ms == pytest.approx(100.0, abs=0.5)

    @pytest.mark.asyncio
    async def test_token_usage_populated(
        self, provider: OllamaProvider, mock_client: MagicMock
    ) -> None:
        request = InferenceRequest(
            model="qwen2.5:1.5b",
            prompt="Test",
            messages=[{"role": "user", "content": "Test"}],
        )
        resp = await provider.generate(request)
        assert resp.usage is not None
        assert resp.usage.prompt_tokens == 15
        assert resp.usage.completion_tokens == 3
        assert resp.usage.total_tokens == 18

    @pytest.mark.asyncio
    async def test_missing_durations_fall_back_to_wall_time(
        self, provider: OllamaProvider, mock_client: MagicMock
    ) -> None:
        """When Ollama omits duration fields, wall clock time is used."""
        raw = _make_ollama_response()
        for key in ["total_duration", "load_duration", "prompt_eval_duration", "eval_duration"]:
            raw.pop(key)
        mock_client.chat = AsyncMock(return_value=raw)

        request = InferenceRequest(
            model="qwen2.5:1.5b",
            prompt="No timings",
            messages=[{"role": "user", "content": "No timings"}],
        )
        resp = await provider.generate(request)
        # Latency should still be a positive number (wall clock)
        assert resp.latency_ms > 0.0

    @pytest.mark.asyncio
    async def test_ollama_prefix_stripped_from_model_id(
        self, provider: OllamaProvider, mock_client: MagicMock
    ) -> None:
        """The 'ollama:' prefix should be stripped before sending to API."""
        captured_payloads = []

        async def capture_chat(payload: dict) -> dict:
            captured_payloads.append(payload)
            return _make_ollama_response()

        mock_client.chat = capture_chat

        request = InferenceRequest(
            model="ollama:llama3.2:3b",
            prompt="Strip prefix",
            messages=[{"role": "user", "content": "Strip prefix"}],
        )
        await provider.generate(request)
        assert captured_payloads[0]["model"] == "llama3.2:3b"

    @pytest.mark.asyncio
    async def test_health_check_delegates_to_client(
        self, provider: OllamaProvider, mock_client: MagicMock
    ) -> None:
        mock_client.check_health = AsyncMock(return_value=True)
        result = await provider.health_check()
        assert result is True
        mock_client.check_health.assert_awaited_once()


class TestOllamaProviderToolCalls:
    """Tests for tool call extraction from Ollama chat responses."""

    @pytest.fixture()
    def mock_client_with_tools(self) -> MagicMock:
        tool_response = _make_ollama_response()
        tool_response["message"] = {
            "role": "assistant",
            "content": "",
            "tool_calls": [
                {
                    "function": {
                        "name": "calculator",
                        "arguments": {"expression": "25 * 4"},
                    }
                }
            ],
        }
        client = MagicMock()
        client.chat = AsyncMock(return_value=tool_response)
        return client

    @pytest.mark.asyncio
    async def test_tool_calls_extracted_from_response(
        self, mock_client_with_tools: MagicMock
    ) -> None:
        provider = OllamaProvider(client=mock_client_with_tools)
        from src.evalforge.providers.schemas import ToolDefinition

        request = InferenceRequest(
            model="qwen2.5:1.5b",
            prompt="Calculate 25 * 4",
            messages=[{"role": "user", "content": "Calculate 25 * 4"}],
            tools=[
                ToolDefinition(
                    name="calculator",
                    description="Evaluate arithmetic expressions",
                    parameters={
                        "type": "object",
                        "properties": {"expression": {"type": "string"}},
                    },
                )
            ],
        )
        resp = await provider.generate(request)
        assert resp.tool_calls is not None
        assert len(resp.tool_calls) == 1
        assert resp.tool_calls[0].name == "calculator"
        assert resp.tool_calls[0].arguments["expression"] == "25 * 4"
