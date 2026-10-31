"""End-to-end integration and verification test for multi-model comparison pipeline."""

from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock

from src.evalforge.evaluators.aggregator import aggregate_scorecard
from src.evalforge.experiments.case_runner import CaseRunner
from src.evalforge.experiments.snapshot import FrozenTestCase
from src.evalforge.providers.schemas import InferenceResponse, TokenUsage
from src.evalforge.schemas.evaluation import EvaluationConfig


class TestMultiModelE2EComparison:
    """Validates complete evaluation-to-metrics pipeline across multiple models."""

    @pytest.mark.asyncio
    async def test_multi_model_pipeline_comparison_and_scorecard_integrity(self) -> None:
        """Run identical test cases through two distinct models and verify isolated 5-metric scorecards."""
        cases = [
            FrozenTestCase(
                id="case-code-1",
                prompt="Write a Python function returning 42.",
                expected_output="def get_answer(): return 42",
                evaluator_config={"assertion_type": "exact_match"},
            ),
            FrozenTestCase(
                id="case-code-2",
                prompt="Write a function returning True.",
                expected_output="def is_valid(): return True",
                evaluator_config={"assertion_type": "exact_match"},
            ),
        ]

        config = EvaluationConfig(metrics=["exact_match"])

        # Model 1 (e.g., qwen2.5:1.5b): fast, both pass
        p1 = MagicMock()
        p1.generate = AsyncMock(
            side_effect=[
                InferenceResponse(
                    text="def get_answer(): return 42",
                    model="qwen2.5:1.5b",
                    provider="ollama",
                    latency_ms=120.0,
                    usage=TokenUsage(prompt_tokens=15, completion_tokens=10, total_tokens=25),
                    raw_metadata={"tokens_per_second": 83.3, "eval_duration_sec": 0.12},
                ),
                InferenceResponse(
                    text="def is_valid(): return True",
                    model="qwen2.5:1.5b",
                    provider="ollama",
                    latency_ms=110.0,
                    usage=TokenUsage(prompt_tokens=12, completion_tokens=8, total_tokens=20),
                    raw_metadata={"tokens_per_second": 72.7, "eval_duration_sec": 0.11},
                ),
            ]
        )
        runner1 = CaseRunner(provider=p1, model_id="qwen2.5:1.5b", config=config)
        results1 = [
            await runner1.execute_case(case=c, evaluation_id="eval-model-1")
            for c in cases
        ]
        scorecard1 = aggregate_scorecard(results1)

        # Model 2 (e.g., qwen2.5:3b): slower, one fails (genuine 0 on second case)
        p2 = MagicMock()
        p2.generate = AsyncMock(
            side_effect=[
                InferenceResponse(
                    text="def get_answer(): return 42",
                    model="qwen2.5:3b",
                    provider="ollama",
                    latency_ms=250.0,
                    usage=TokenUsage(prompt_tokens=15, completion_tokens=10, total_tokens=25),
                    raw_metadata={"tokens_per_second": 40.0, "eval_duration_sec": 0.25},
                ),
                InferenceResponse(
                    text="def invalid(): pass",
                    model="qwen2.5:3b",
                    provider="ollama",
                    latency_ms=230.0,
                    usage=TokenUsage(prompt_tokens=12, completion_tokens=6, total_tokens=18),
                    raw_metadata={"tokens_per_second": 26.0, "eval_duration_sec": 0.23},
                ),
            ]
        )
        runner2 = CaseRunner(provider=p2, model_id="qwen2.5:3b", config=config)
        results2 = [
            await runner2.execute_case(case=c, evaluation_id="eval-model-2")
            for c in cases
        ]
        scorecard2 = aggregate_scorecard(results2)

        # 1. Model Accuracy Comparison
        assert scorecard1.pass_rate == 1.0  # 100%
        assert scorecard2.pass_rate == 0.5  # 50%

        # 2. Average Latency Comparison
        assert scorecard1.avg_latency_ms == pytest.approx(115.0, rel=1e-2)
        assert scorecard2.avg_latency_ms == pytest.approx(240.0, rel=1e-2)
        assert scorecard1.avg_latency_ms < scorecard2.avg_latency_ms

        # 3. Throughput Comparison (avg_tokens_per_second)
        assert scorecard1.avg_tokens_per_second is not None
        assert scorecard2.avg_tokens_per_second is not None
        assert scorecard1.avg_tokens_per_second > scorecard2.avg_tokens_per_second

        # 4. Efficiency Comparison (Throughput / Latency * 1000)
        eff1 = (scorecard1.avg_tokens_per_second / scorecard1.avg_latency_ms) * 1000
        eff2 = (scorecard2.avg_tokens_per_second / scorecard2.avg_latency_ms) * 1000
        assert eff1 > eff2

        # 5. Success / Failure Summary
        assert scorecard1.passed_cases == 2
        assert scorecard1.failed_cases == 0
        assert scorecard2.passed_cases == 1
        assert scorecard2.failed_cases == 1

        # Check genuine zero distinction on executed failed case (not an error crash)
        assert results2[1].passed is False
        assert results2[1].error_message is None
        exact_match_metric = results2[1].metrics.get("exact_match")
        assert exact_match_metric is not None
        assert exact_match_metric["score"] == 0.0
        assert exact_match_metric["passed"] is False
