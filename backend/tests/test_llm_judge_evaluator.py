"""Unit tests for LLMJudgeEvaluator — score parsing, fallback regex, and provenance metadata."""

from unittest.mock import AsyncMock, MagicMock
import pytest

from src.evalforge.evaluators.llm_judge import LLMJudgeEvaluator
from src.evalforge.providers.schemas import InferenceResponse


class TestLLMJudgeEvaluator:
    """Verifies that model-assisted evaluation formats prompts, parses judgments, and flags estimates."""

    @pytest.mark.asyncio
    async def test_perfect_score_parsed_from_json(self) -> None:
        mock_provider = MagicMock()
        mock_provider.name = "mock_provider"
        mock_provider.generate = AsyncMock(
            return_value=InferenceResponse(
                text='{"score": 5, "reasoning": "Candidate answer is accurate and complete."}',
                model="mock-llama-3.1-8b",
                provider="mock_provider",
                latency_ms=100.0,
            )
        )

        judge = LLMJudgeEvaluator(provider=mock_provider, judge_model="mock-llama-3.1-8b")
        res = await judge.evaluate(prediction="4", reference="4", context="2+2")

        assert res.passed is True
        assert res.score == 1.0  # (5 - 1) / 4 = 1.0
        assert res.method == "llm_as_judge_estimate"
        assert res.details["is_estimate"] is True
        assert res.details["raw_score_1_to_5"] == 5
        assert "Candidate answer is accurate" in res.details["reasoning"]
        assert "not an objective ground truth" in res.details["disclaimer"]

    @pytest.mark.asyncio
    async def test_failing_score_parsed_correctly(self) -> None:
        mock_provider = MagicMock()
        mock_provider.name = "mock_provider"
        mock_provider.generate = AsyncMock(
            return_value=InferenceResponse(
                text='{"score": 2, "reasoning": "Missed the key instruction."}',
                model="mock-llama-3.1-8b",
                provider="mock_provider",
                latency_ms=100.0,
            )
        )

        judge = LLMJudgeEvaluator(provider=mock_provider, judge_model="mock-llama-3.1-8b")
        res = await judge.evaluate(prediction="wrong", reference="correct")

        assert res.passed is False
        assert res.score == 0.25  # (2 - 1) / 4 = 0.25
        assert res.details["raw_score_1_to_5"] == 2

    @pytest.mark.asyncio
    async def test_fallback_to_digit_regex_on_malformed_json(self) -> None:
        mock_provider = MagicMock()
        mock_provider.name = "mock_provider"
        mock_provider.generate = AsyncMock(
            return_value=InferenceResponse(
                text="I would give this output a rating of 4 out of 5 because it was mostly fine.",
                model="mock-llama-3.1-8b",
                provider="mock_provider",
                latency_ms=100.0,
            )
        )

        judge = LLMJudgeEvaluator(provider=mock_provider, judge_model="mock-llama-3.1-8b")
        res = await judge.evaluate(prediction="good output", reference="perfect output")

        assert res.score == 0.75  # (4 - 1) / 4 = 0.75
        assert res.passed is True
        assert res.details["raw_score_1_to_5"] == 4

    @pytest.mark.asyncio
    async def test_unparseable_output_defaults_to_neutral_three(self) -> None:
        mock_provider = MagicMock()
        mock_provider.name = "mock_provider"
        mock_provider.generate = AsyncMock(
            return_value=InferenceResponse(
                text="Random garbled text without digits.",
                model="mock-llama-3.1-8b",
                provider="mock_provider",
                latency_ms=100.0,
            )
        )

        judge = LLMJudgeEvaluator(provider=mock_provider, judge_model="mock-llama-3.1-8b")
        res = await judge.evaluate(prediction="test", reference="test")

        assert res.details["raw_score_1_to_5"] == 3
        assert res.score == 0.5  # (3 - 1) / 4 = 0.5
        assert res.passed is False  # threshold is 0.6
