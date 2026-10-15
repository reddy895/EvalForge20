"""Unit tests for composite evaluator with weighted scoring and component transparency."""

import pytest
from app.domain.contracts import EvaluatorInput
from app.domain.errors import EvaluatorError
from app.domain.models import EvaluationCase
from app.evaluators.composite.scorer import CompositeEvaluator
from app.evaluators.registry import registry


@pytest.mark.asyncio
async def test_composite_evaluator_success():
    evaluator = CompositeEvaluator()
    case = EvaluationCase(id="c1", input="hello", expected_output='{"status": "ok"}')
    eval_input = EvaluatorInput(
        case=case,
        actual_output='{"status": "ok"}',
        options={
            "weights": {"exact_match": 0.6, "json_validity": 0.4},
            "threshold": 0.8,
        },
    )
    result = await evaluator.evaluate(eval_input)

    assert result.score == 1.0
    assert result.passed is True
    assert "exact_match" in result.details["component_scores"]
    assert "json_validity" in result.details["component_scores"]
    assert result.details["component_scores"]["exact_match"] == 1.0
    assert result.details["component_scores"]["json_validity"] == 1.0


@pytest.mark.asyncio
async def test_composite_evaluator_partial_and_component_failure():
    evaluator = CompositeEvaluator()
    case = EvaluationCase(id="c2", input="hello", expected_output="completely different")
    # Output matches JSON validity, but fails exact match
    eval_input = EvaluatorInput(
        case=case,
        actual_output='{"status": "ok"}',
        options={
            "weights": {"exact_match": 0.5, "json_validity": 0.5},
            "threshold": 0.4,
        },
    )
    result = await evaluator.evaluate(eval_input)

    # exact_match score is 0.0, json_validity score is 1.0 -> weighted average is 0.5
    assert result.score == 0.5
    # Even though 0.5 >= threshold 0.4, exact_match passed=False, so hard failure is preserved!
    assert result.passed is False
    assert result.details["component_passed"]["exact_match"] is False
    assert result.details["component_passed"]["json_validity"] is True


@pytest.mark.asyncio
async def test_composite_evaluator_missing_component_handling():
    evaluator = CompositeEvaluator()
    case = EvaluationCase(id="c3", input="hello")
    eval_input = EvaluatorInput(
        case=case,
        actual_output="hello",
        options={
            "weights": {"exact_match": 0.5, "non_existent_metric": 0.5},
            "require_all": True,
        },
    )
    result = await evaluator.evaluate(eval_input)
    assert result.score is None
    assert result.passed is False
    assert "non_existent_metric" in result.details["missing_components"]


@pytest.mark.asyncio
async def test_composite_evaluator_invalid_weights():
    evaluator = CompositeEvaluator()
    case = EvaluationCase(id="c4", input="hello")
    eval_input = EvaluatorInput(
        case=case,
        actual_output="hello",
        options={"weights": {"exact_match": -0.5}},
    )
    with pytest.raises(EvaluatorError, match="non-negative"):
        await evaluator.evaluate(eval_input)


def test_composite_evaluator_registered():
    assert "composite_score" in registry.list_metric_ids()
