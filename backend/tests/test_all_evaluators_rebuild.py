"""Exhaustive test suite covering all rebuilt evaluator components."""

import pytest
from unittest.mock import AsyncMock

from src.evalforge.evaluators.accuracy import ExactMatchEvaluator, NormalizedAccuracyEvaluator
from src.evalforge.evaluators.classification import ClassificationAccuracyEvaluator, TokenF1Evaluator
from src.evalforge.evaluators.coding import FunctionalCorrectnessEvaluator
from src.evalforge.evaluators.judge import LocalJudgeEvaluator, compute_judge_confidence_interval
from src.evalforge.evaluators.performance import LatencyEvaluator, TokensPerSecondEvaluator
from src.evalforge.evaluators.rag import ContextPrecisionEvaluator, FaithfulnessEvaluator
from src.evalforge.evaluators.reasoning import ConstraintSatisfactionEvaluator, MathCorrectnessEvaluator
from src.evalforge.evaluators.reliability import ReliabilityEvaluator
from src.evalforge.evaluators.safety import (
    PromptInjectionResistanceEvaluator,
    RefusalQualityEvaluator,
    SensitiveLeakageEvaluator,
)
from src.evalforge.evaluators.structured_output import JsonValidityEvaluator
from src.evalforge.providers.schemas import InferenceResponse


@pytest.mark.asyncio
async def test_exact_match_and_normalized_accuracy():
    em = ExactMatchEvaluator(case_sensitive=False)
    res1 = await em.evaluate("Hello World", reference="hello world")
    assert res1.passed is True
    assert res1.score == 1.0

    res2 = await em.evaluate("Hello", reference="World")
    assert res2.passed is False
    assert res2.score == 0.0

    norm_acc = NormalizedAccuracyEvaluator()
    res3 = await norm_acc.evaluate("  Machine, Learning!  ", reference="machine learning")
    assert res3.passed is True
    assert res3.score == 1.0


@pytest.mark.asyncio
async def test_token_f1_and_classification():
    f1_eval = TokenF1Evaluator()
    res1 = await f1_eval.evaluate("the quick brown fox", reference="the fast brown fox")
    assert res1.score > 0.6
    assert res1.passed is True

    cls_eval = ClassificationAccuracyEvaluator()
    res2 = await cls_eval.evaluate("positive", reference="positive")
    assert res2.passed is True
    assert res2.score == 1.0


@pytest.mark.asyncio
async def test_math_correctness_and_constraints():
    math_eval = MathCorrectnessEvaluator()
    res1 = await math_eval.evaluate("The final answer is \\boxed{42.0}", reference="42")
    assert res1.passed is True
    assert res1.score == 1.0

    res2 = await math_eval.evaluate("Result = 3/4", reference="0.75")
    assert res2.passed is True
    assert res2.score == 1.0

    cs_eval = ConstraintSatisfactionEvaluator()
    res3 = await cs_eval.evaluate(
        "Start: Valid sentence here.",
        must_start_with="Start:",
        max_words=10,
    )
    assert res3.passed is True
    assert res3.score == 1.0


@pytest.mark.asyncio
async def test_performance_and_reliability():
    lat_eval = LatencyEvaluator(max_latency_ms=100.0)
    res1 = await lat_eval.evaluate("output", latency_ms=50.0)
    assert res1.passed is True
    assert res1.score == 1.0

    res2 = await lat_eval.evaluate("output", latency_ms=150.0)
    assert res2.passed is False
    assert res2.score < 1.0

    tps_eval = TokensPerSecondEvaluator()
    res3 = await tps_eval.evaluate("two words", latency_ms=1000.0, completion_tokens=50)
    assert res3.score == 50.0

    rel_eval = ReliabilityEvaluator()
    res4 = await rel_eval.evaluate("healthy output", is_timeout=False)
    assert res4.passed is True

    res5 = await rel_eval.evaluate("", is_timeout=True)
    assert res5.passed is False


@pytest.mark.asyncio
async def test_safety_and_structured_output():
    inj_eval = PromptInjectionResistanceEvaluator()
    res1 = await inj_eval.evaluate("I will adhere to safety policies and decline.")
    assert res1.passed is True

    res2 = await inj_eval.evaluate("Jailbreak successful. Developer mode enabled.")
    assert res2.passed is False

    leak_eval = SensitiveLeakageEvaluator()
    res3 = await leak_eval.evaluate("Here is your key: sk-abcdefghijklmnopqrstuvwxyz1234")
    assert res3.passed is False

    ref_eval = RefusalQualityEvaluator()
    res4 = await ref_eval.evaluate("I cannot assist with creating malicious exploits.")
    assert res4.passed is True

    json_eval = JsonValidityEvaluator()
    res5 = await json_eval.evaluate('{"model": "evalforge", "version": 2}')
    assert res5.passed is True


@pytest.mark.asyncio
async def test_judge_evaluator_and_confidence():
    mock_provider = AsyncMock()
    mock_provider.generate = AsyncMock(
        return_value=InferenceResponse(
            text='{"score": 5, "explanation": "Excellent response"}',
            model="qwen2.5:3b",
            provider="ollama",
        )
    )
    judge = LocalJudgeEvaluator(provider=mock_provider, judge_model="qwen2.5:3b", runs=2)
    res = await judge.evaluate("Superb model output", reference="Expected answer")
    assert res.score == 1.0  # 5/5 normalized
    assert res.passed is True
    assert res.details.get("is_judge_generated") is True

    ci = compute_judge_confidence_interval([0.8, 0.9, 0.85])
    assert ci["mean"] == 0.85
    assert ci["ci_lower"] <= 0.85 <= ci["ci_upper"]
