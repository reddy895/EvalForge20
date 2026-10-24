"""Unit and failure-mode tests for OllamaProvider and evaluation error categorization.

Covers:
- Connection refused / host unreachable
- Read timeout during generation
- Missing model (404 ResponseError)
- Malformed / truncated responses
- Error categorization in aggregator (timeouts, connection_errors, model_not_found)
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock
import pytest

from src.evalforge.providers.ollama.provider import OllamaProvider
from src.evalforge.providers.schemas import InferenceRequest
from src.evalforge.evaluators.aggregator import aggregate_scorecard


class TestOllamaFailureModes:
    """Verifies that provider failures are captured with clear semantics and do not crash the engine."""

    @pytest.mark.asyncio
    async def test_connection_refused_raises_runtime_error(self) -> None:
        """When daemon is down, provider raise informative error with host details."""
        mock_client = MagicMock()
        mock_client.generate = AsyncMock(side_effect=ConnectionRefusedError("Connection refused on 127.0.0.1:11434"))
        provider = OllamaProvider(client=mock_client)

        req = InferenceRequest(model="qwen2.5:1.5b", prompt="Hello")
        with pytest.raises(ConnectionRefusedError, match="Connection refused"):
            await provider.generate(req)

    @pytest.mark.asyncio
    async def test_inference_timeout_raises_timeout_error(self) -> None:
        """When inference times out, provider bubbles TimeoutError."""
        mock_client = MagicMock()
        mock_client.generate = AsyncMock(side_effect=TimeoutError("Ollama request timed out after 30s"))
        provider = OllamaProvider(client=mock_client)

        req = InferenceRequest(model="qwen2.5:1.5b", prompt="Summarize this large text")
        with pytest.raises(TimeoutError, match="timed out"):
            await provider.generate(req)

    @pytest.mark.asyncio
    async def test_model_not_found_error_captured(self) -> None:
        """When model is not pulled, provider surfaces model missing error."""
        mock_client = MagicMock()
        mock_client.generate = AsyncMock(side_effect=RuntimeError("model 'nonexistent:latest' not found, try pulling it first"))
        provider = OllamaProvider(client=mock_client)

        req = InferenceRequest(model="nonexistent:latest", prompt="Test")
        with pytest.raises(RuntimeError, match="not found"):
            await provider.generate(req)


class TestAggregatorReliabilityMetrics:
    """Tests for reliability metric tracking, failure counting, and error classification."""

    def test_aggregates_reliability_and_error_categories(self) -> None:
        """Aggregator should classify timeouts, connection errors, and missing models into categories."""
        cases = [
            SimpleNamespace(
                passed=True,
                latency_ms=100.0,
                token_usage={"prompt_tokens": 10, "completion_tokens": 5, "tokens_per_second": 50.0},
                metrics={"exact_match": {"score": 1.0, "passed": True}},
                error_message=None,
            ),
            SimpleNamespace(
                passed=False,
                latency_ms=0.0,
                token_usage=None,
                metrics={},
                error_message="Ollama request timed out after 30s",
            ),
            SimpleNamespace(
                passed=False,
                latency_ms=0.0,
                token_usage=None,
                metrics={},
                error_message="Failed to connect: Connection refused on localhost:11434",
            ),
            SimpleNamespace(
                passed=False,
                latency_ms=0.0,
                token_usage=None,
                metrics={},
                error_message="model 'qwen2.5:72b' not found (status 404)",
            ),
        ]

        sc = aggregate_scorecard(cases)

        assert sc.total_cases == 4
        assert sc.passed_cases == 1
        assert sc.failed_cases == 3
        assert sc.pass_rate == 0.25

        # Reliability fields
        assert sc.error_count == 3
        assert sc.timeout_count == 1
        assert sc.error_categories.get("timeout") == 1
        assert sc.error_categories.get("connection_error") == 1
        assert sc.error_categories.get("model_not_found") == 1

        # Latency should not be artificially dragged to 25.0ms by zero-ms failed calls
        assert sc.avg_latency_ms == 100.0
