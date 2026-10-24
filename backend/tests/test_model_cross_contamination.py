"""Regression test suite for multi-model evaluation isolation and cross-contamination prevention.

Ensures that evaluating multiple models concurrently or sequentially:
1. Keeps individual model metrics strictly isolated (no shared references or collapsed results).
2. Preserves distinct latency, throughput, token counts, and accuracy scores per model.
3. Correctly binds model_id, run_id, and provider identifiers without cross-talk.
4. Correctly preserves genuinely equal measurements without artificial noise.
"""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.evalforge.evaluators.aggregator import aggregate_scorecard
from src.evalforge.experiments.case_runner import CaseRunner
from src.evalforge.experiments.snapshot import FrozenTestCase
from src.evalforge.providers.schemas import InferenceResponse, TokenUsage
from src.evalforge.schemas.evaluation import EvaluationConfig


class TestModelCrossContamination:
    """Validates that distinct models maintain isolated evaluation state and distinct metrics."""

    @pytest.mark.asyncio
    async def test_distinct_models_preserve_distinct_telemetry(self) -> None:
        """Evaluate 3 simulated models with distinct speeds and accuracies; ensure no leakage."""
        case = FrozenTestCase(
            id="case-math-1",
            prompt="What is 15 * 4?",
            expected_output="60",
            evaluator_config={"assertion_type": "exact_match"},
        )

        config = EvaluationConfig(metrics=["exact_match"])

        # Model A: Fast, 100% correct
        resp_a = InferenceResponse(
            text="60",
            model="llama3.2:1b",
            provider="ollama",
            latency_ms=45.0,
            usage=TokenUsage(prompt_tokens=10, completion_tokens=3, total_tokens=13),
            raw_metadata={"tokens_per_second": 66.7, "eval_duration_sec": 0.045},
        )
        provider_a = MagicMock()
        provider_a.generate = AsyncMock(return_value=resp_a)
        runner_a = CaseRunner(provider=provider_a, model_id="llama3.2:1b", config=config)

        # Model B: Slower, correct
        resp_b = InferenceResponse(
            text="60",
            model="mistral:7b",
            provider="ollama",
            latency_ms=210.0,
            usage=TokenUsage(prompt_tokens=10, completion_tokens=8, total_tokens=18),
            raw_metadata={"tokens_per_second": 38.1, "eval_duration_sec": 0.210},
        )
        provider_b = MagicMock()
        provider_b.generate = AsyncMock(return_value=resp_b)
        runner_b = CaseRunner(provider=provider_b, model_id="mistral:7b", config=config)

        # Model C: Fast, incorrect
        resp_c = InferenceResponse(
            text="The answer is 50",
            model="qwen2.5:0.5b",
            provider="ollama",
            latency_ms=30.0,
            usage=TokenUsage(prompt_tokens=10, completion_tokens=5, total_tokens=15),
            raw_metadata={"tokens_per_second": 166.7, "eval_duration_sec": 0.030},
        )
        provider_c = MagicMock()
        provider_c.generate = AsyncMock(return_value=resp_c)
        runner_c = CaseRunner(provider=provider_c, model_id="qwen2.5:0.5b", config=config)

        # Execute each case
        res_a = await runner_a.execute_case(case=case, evaluation_id="eval-a")
        res_b = await runner_b.execute_case(case=case, evaluation_id="eval-b")
        res_c = await runner_c.execute_case(case=case, evaluation_id="eval-c")

        # 1. Assertions on individual cases
        assert res_a.passed is True
        assert res_b.passed is True
        assert res_c.passed is False

        assert res_a.latency_ms == pytest.approx(45.0, abs=1.0)
        assert res_b.latency_ms == pytest.approx(210.0, abs=1.0)
        assert res_c.latency_ms == pytest.approx(30.0, abs=1.0)

        # Assert independent objects and distinct metadata
        assert res_a.token_usage["tokens_per_second"] == 66.7
        assert res_b.token_usage["tokens_per_second"] == 38.1
        assert res_c.token_usage["tokens_per_second"] == 166.7

        # 2. Aggregation isolation
        sc_a = aggregate_scorecard([res_a])
        sc_b = aggregate_scorecard([res_b])
        sc_c = aggregate_scorecard([res_c])

        assert sc_a.pass_rate == 1.0
        assert sc_b.pass_rate == 1.0
        assert sc_c.pass_rate == 0.0

        assert sc_a.avg_latency_ms == pytest.approx(45.0, abs=1.0)
        assert sc_b.avg_latency_ms == pytest.approx(210.0, abs=1.0)
        assert sc_c.avg_latency_ms == pytest.approx(30.0, abs=1.0)

        assert sc_a.avg_tokens_per_second == 66.7
        assert sc_b.avg_tokens_per_second == 38.1
        assert sc_c.avg_tokens_per_second == 166.7

    @pytest.mark.asyncio
    async def test_genuinely_equal_models_are_preserved_not_distorted(self) -> None:
        """When two models legitimately return identical outputs and timings, system preserves them."""
        case = FrozenTestCase(
            id="case-1",
            prompt="Echo: test",
            expected_output="test",
            evaluator_config={"assertion_type": "exact_match"},
        )
        config = EvaluationConfig(metrics=["exact_match"])

        resp_twin1 = InferenceResponse(
            text="test",
            model="model-clone-1",
            provider="ollama",
            latency_ms=50.0,
            usage=TokenUsage(prompt_tokens=5, completion_tokens=2, total_tokens=7),
            raw_metadata={"tokens_per_second": 40.0},
        )
        resp_twin2 = InferenceResponse(
            text="test",
            model="model-clone-2",
            provider="ollama",
            latency_ms=50.0,
            usage=TokenUsage(prompt_tokens=5, completion_tokens=2, total_tokens=7),
            raw_metadata={"tokens_per_second": 40.0},
        )

        p1 = MagicMock()
        p1.generate = AsyncMock(return_value=resp_twin1)
        runner1 = CaseRunner(provider=p1, model_id="model-clone-1", config=config)

        p2 = MagicMock()
        p2.generate = AsyncMock(return_value=resp_twin2)
        runner2 = CaseRunner(provider=p2, model_id="model-clone-2", config=config)

        res1 = await runner1.execute_case(case=case, evaluation_id="eval-1")
        res2 = await runner2.execute_case(case=case, evaluation_id="eval-2")

        # Must be equal without artificial random variation
        assert res1.latency_ms == pytest.approx(res2.latency_ms, abs=1.0)
        assert res1.passed == res2.passed is True
        assert res1.evaluation_id != res2.evaluation_id

    @pytest.mark.asyncio
    async def test_concurrent_evaluations_do_not_interleave_shared_state(self) -> None:
        """Verify that concurrent async evaluation runs do not mutate or cross-contaminate state."""
        config = EvaluationConfig(metrics=["exact_match"])

        async def run_simulated_model(model_name: str, score_expected: float, delay_ms: float) -> float:
            case = FrozenTestCase(
                id=f"case-{model_name}",
                prompt=f"Prompt for {model_name}",
                expected_output="OK",
                evaluator_config={"assertion_type": "exact_match"},
            )
            provider = MagicMock()
            await asyncio.sleep(delay_ms / 1000.0)
            provider.generate = AsyncMock(return_value=InferenceResponse(
                text="OK" if score_expected > 0.5 else "FAIL",
                model=model_name,
                provider="ollama",
                latency_ms=delay_ms,
                usage=TokenUsage(prompt_tokens=10, completion_tokens=5, total_tokens=15),
                raw_metadata={"tokens_per_second": 50.0},
            ))
            runner = CaseRunner(provider=provider, model_id=model_name, config=config)
            res = await runner.execute_case(case=case, evaluation_id=f"eval-{model_name}")
            return res.latency_ms

        results = await asyncio.gather(
            run_simulated_model("model-fast", 1.0, 10.0),
            run_simulated_model("model-mid", 1.0, 30.0),
            run_simulated_model("model-slow", 0.0, 60.0),
        )

        assert results[0] == pytest.approx(10.0, abs=1.0)
        assert results[1] == pytest.approx(30.0, abs=1.0)
        assert results[2] == pytest.approx(60.0, abs=1.0)
