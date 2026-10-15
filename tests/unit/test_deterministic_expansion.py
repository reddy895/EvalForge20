"""Unit tests for expanded deterministic metrics (Token F1, Classification, Response Completeness)."""

import pytest
from app.domain.contracts import EvaluatorInput
from app.domain.models import EvaluationCase
from app.evaluators.code.classification import ClassificationAccuracyEvaluator
from app.evaluators.code.completeness import ResponseCompletenessEvaluator
from app.evaluators.code.token_f1 import TokenF1Evaluator
from app.evaluators.registry import registry


@pytest.mark.asyncio
async def test_token_f1_evaluator():
    evaluator = TokenF1Evaluator()

    # 1. Exact match sequence
    case1 = EvaluationCase(id="t1", input="question", expected_output="The quick brown fox jumps.")
    res1 = await evaluator.evaluate(
        EvaluatorInput(case=case1, actual_output="The quick brown fox jumps.")
    )
    assert res1.score == 1.0
    assert res1.passed is True

    # 2. Partial overlap: 2 words overlap out of 4 and 4 -> F1 = 0.5
    case2 = EvaluationCase(id="t2", input="question", expected_output="apple banana cherry date")
    res2 = await evaluator.evaluate(
        EvaluatorInput(case=case2, actual_output="apple banana grape fig")
    )
    assert res2.score == 0.5
    assert res2.details["overlap_tokens"] == 2

    # 3. Disjoint
    case3 = EvaluationCase(id="t3", input="question", expected_output="paris france")
    res3 = await evaluator.evaluate(EvaluatorInput(case=case3, actual_output="tokyo japan"))
    assert res3.score == 0.0
    assert res3.passed is False

    # 4. Missing expected output
    case4 = EvaluationCase(id="t4", input="question")
    res4 = await evaluator.evaluate(EvaluatorInput(case=case4, actual_output="anything"))
    assert res4.score is None


@pytest.mark.asyncio
async def test_classification_accuracy_evaluator():
    evaluator = ClassificationAccuracyEvaluator()

    # 1. Direct label match
    case1 = EvaluationCase(id="c1", input="I love this!", expected_output="positive")
    res1 = await evaluator.evaluate(EvaluatorInput(case=case1, actual_output="positive"))
    assert res1.score == 1.0
    assert res1.passed is True

    # 2. Conversational prefix with markdown
    case2 = EvaluationCase(id="c2", input="Terrible service", expected_output="negative")
    res2 = await evaluator.evaluate(
        EvaluatorInput(case=case2, actual_output="The classification is: **negative**.")
    )
    assert res2.score == 1.0
    assert res2.passed is True

    # 3. Mismatch
    case3 = EvaluationCase(id="c3", input="text", expected_output="spam")
    res3 = await evaluator.evaluate(EvaluatorInput(case=case3, actual_output="ham"))
    assert res3.score == 0.0
    assert res3.passed is False


@pytest.mark.asyncio
async def test_response_completeness_evaluator():
    evaluator = ResponseCompletenessEvaluator()

    # 1. Clean complete sentence
    case1 = EvaluationCase(id="r1", input="Explain photosynthesis")
    res1 = await evaluator.evaluate(
        EvaluatorInput(case=case1, actual_output="Photosynthesis converts light into glucose.")
    )
    assert res1.score == 1.0
    assert res1.passed is True

    # 2. Truncated sentence without terminal punctuation
    res2 = await evaluator.evaluate(
        EvaluatorInput(
            case=case1,
            actual_output="Photosynthesis converts light into chemical energy which is stored in",
        )
    )
    assert res2.score == 0.7  # flag potential cut-off
    assert res2.details["is_terminated"] is False

    # 3. Empty response
    res3 = await evaluator.evaluate(EvaluatorInput(case=case1, actual_output=""))
    assert res3.score == 0.0
    assert res3.passed is False


def test_expanded_metrics_registered():
    assert registry.is_registered("token_f1")
    assert registry.is_registered("classification_accuracy")
    assert registry.is_registered("response_completeness")
