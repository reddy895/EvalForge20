"""Unit tests for NumericToleranceEvaluator arithmetic precision and tolerance comparison."""

import pytest

from src.evalforge.evaluators.deterministic.numeric_tolerance import NumericToleranceEvaluator


@pytest.mark.asyncio
async def test_numeric_tolerance_exact_match() -> None:
    evaluator = NumericToleranceEvaluator()
    res = await evaluator.evaluate(prediction="42.0", reference="42.0")
    assert res.passed is True
    assert res.score == 1.0
    assert res.details["expected"] == 42.0


@pytest.mark.asyncio
async def test_numeric_tolerance_within_tolerance() -> None:
    # 100.0 with 0.01 tolerance allows 99.99 to 100.01
    evaluator = NumericToleranceEvaluator(atol=1e-3, rtol=1e-3)
    res = await evaluator.evaluate(prediction="The velocity is 100.05 m/s", reference="100.0")
    # 0.05 > 0.001 + 0.001*100 = 0.101 -> within tolerance!
    assert res.passed is True
    assert res.score == 1.0


@pytest.mark.asyncio
async def test_numeric_tolerance_outside_tolerance() -> None:
    evaluator = NumericToleranceEvaluator(atol=1e-4, rtol=1e-4)
    res = await evaluator.evaluate(prediction="Answer: 45.5", reference="42.0")
    assert res.passed is False
    assert res.score == 0.0
    assert res.details["difference"] == 3.5


@pytest.mark.asyncio
async def test_numeric_tolerance_no_numbers_in_prediction() -> None:
    evaluator = NumericToleranceEvaluator()
    res = await evaluator.evaluate(prediction="No number here", reference="10.0")
    assert res.passed is False
    assert res.score == 0.0
    assert "error" in res.details


@pytest.mark.asyncio
async def test_numeric_tolerance_missing_reference() -> None:
    evaluator = NumericToleranceEvaluator()
    res = await evaluator.evaluate(prediction="10.0", reference=None)
    assert res.passed is False
    assert res.score == 0.0
    assert "error" in res.details
