"""Comprehensive test suite for deterministic and model-assisted metrics."""

import pytest

from src.evalforge.evaluators.aggregator import aggregate_scorecard, compute_percentile
from src.evalforge.evaluators.deterministic.exact_match import (
    ExactMatchEvaluator,
    NormalizedExactMatchEvaluator,
)
from src.evalforge.evaluators.deterministic.json_schema import JsonSchemaEvaluator
from src.evalforge.evaluators.deterministic.keywords import KeywordEvaluator
from src.evalforge.evaluators.deterministic.performance import LatencySlaEvaluator
from src.evalforge.evaluators.deterministic.token_f1 import TokenF1Evaluator
from src.evalforge.evaluators.llm_judge import LLMJudgeEvaluator
from src.evalforge.evaluators.semantic import SemanticSimilarityEvaluator
from src.evalforge.providers.mock import MockProvider
from src.evalforge.storage.models.evaluation import CaseResult


@pytest.mark.asyncio
async def test_exact_match_evaluator() -> None:
    evaluator = ExactMatchEvaluator()

    # Match with surrounding whitespace
    res = await evaluator.evaluate(" Paris  ", reference="Paris")
    assert res.score == 1.0
    assert res.passed is True

    # Strict mismatch (casing)
    res_case = await evaluator.evaluate("paris", reference="Paris")
    assert res_case.score == 0.0
    assert res_case.passed is False

    # Missing reference
    res_none = await evaluator.evaluate("Paris", reference=None)
    assert res_none.score == 0.0
    assert res_none.passed is False


@pytest.mark.asyncio
async def test_normalized_exact_match_evaluator() -> None:
    evaluator = NormalizedExactMatchEvaluator()

    # Case, punctuation, and article tolerance
    res = await evaluator.evaluate("The Eiffel Tower, Paris!", reference="eiffel tower paris")
    assert res.score == 1.0
    assert res.passed is True

    # Real mismatch
    res_diff = await evaluator.evaluate("Berlin", reference="Paris")
    assert res_diff.score == 0.0
    assert res_diff.passed is False


@pytest.mark.asyncio
async def test_token_f1_evaluator() -> None:
    evaluator = TokenF1Evaluator()

    # Full overlap
    res_full = await evaluator.evaluate("quick brown fox", reference="quick brown fox")
    assert res_full.score == 1.0
    assert res_full.passed is True

    # Partial overlap
    res_part = await evaluator.evaluate("quick brown dog", reference="quick brown fox")
    assert 0.6 < res_part.score < 0.7
    assert round(res_part.details["precision"], 2) == 0.67
    assert round(res_part.details["recall"], 2) == 0.67

    # Disjoint
    res_zero = await evaluator.evaluate("apple orange", reference="car bus")
    assert res_zero.score == 0.0
    assert res_zero.passed is False


@pytest.mark.asyncio
async def test_keyword_evaluator() -> None:
    evaluator = KeywordEvaluator()

    # Required present
    res_req = await evaluator.evaluate(
        "Python is an interpreted, high-level programming language.",
        required_keywords=["Python", "high-level"],
    )
    assert res_req.score == 1.0
    assert res_req.passed is True

    # Missing required
    res_missing = await evaluator.evaluate(
        "Python is interpreted.",
        required_keywords=["Python", "compiled"],
    )
    assert res_missing.score == 0.5
    assert res_missing.passed is False
    assert "compiled" in res_missing.details["missing_required"]

    # Prohibited violation
    res_proh = await evaluator.evaluate(
        "System crashed due to internal database timeout error.",
        required_keywords=["database"],
        prohibited_keywords=["timeout error"],
    )
    assert res_proh.score == 0.0
    assert res_proh.passed is False
    assert "timeout error" in res_proh.details["found_prohibited"]


@pytest.mark.asyncio
async def test_json_schema_evaluator() -> None:
    evaluator = JsonSchemaEvaluator()

    schema = {
        "type": "object",
        "properties": {
            "city": {"type": "string"},
            "population": {"type": "integer"},
            "is_capital": {"type": "boolean"},
        },
        "required": ["city", "population"],
    }

    # Valid in markdown code fence
    fence_output = """Here is the city information:
```json
{
  "city": "Tokyo",
  "population": 14000000,
  "is_capital": true
}
```
"""
    res_fence = await evaluator.evaluate(fence_output, schema=schema)
    assert res_fence.score == 1.0
    assert res_fence.passed is True

    # Missing required field
    missing_output = '{"city": "Paris"}'
    res_miss = await evaluator.evaluate(missing_output, schema=schema)
    assert res_miss.score == 0.5
    assert res_miss.passed is False
    assert "population" in res_miss.details["missing_fields"]

    # Invalid JSON syntax
    bad_syntax = "{not valid json"
    res_bad = await evaluator.evaluate(bad_syntax, schema=schema)
    assert res_bad.score == 0.0
    assert res_bad.passed is False
    assert res_bad.details["is_valid_json"] is False


@pytest.mark.asyncio
async def test_latency_sla_evaluator() -> None:
    evaluator = LatencySlaEvaluator()

    res_good = await evaluator.evaluate(
        "Output", latency_ms=450.0, max_latency_ms=1000.0, completion_tokens=50
    )
    assert res_good.score == 1.0
    assert res_good.passed is True
    assert res_good.details["throughput_tokens_per_sec"] is not None

    res_slow = await evaluator.evaluate("Output", latency_ms=1500.0, max_latency_ms=1000.0)
    assert res_slow.score < 1.0
    assert res_slow.passed is False


@pytest.mark.asyncio
async def test_llm_judge_evaluator_with_mock() -> None:
    mock = MockProvider(
        canned_responses={".*": '{"score": 5, "reasoning": "Excellent mathematical deduction"}'}
    )
    evaluator = LLMJudgeEvaluator(provider=mock, judge_model="mock-llama-3.1-8b")

    res = await evaluator.evaluate(
        prediction="Step 1: 5 * 5 = 25. Step 2: 25 + 5 = 30.",
        reference="The final total is 30.",
    )
    assert res.score == 1.0
    assert res.passed is True
    assert res.details["is_estimate"] is True
    assert "disclaimer" in res.details
    assert "reasoning" in res.details


@pytest.mark.asyncio
async def test_semantic_similarity_evaluator() -> None:
    evaluator = SemanticSimilarityEvaluator()

    res_high = await evaluator.evaluate(
        "The quick brown fox jumps over the dog",
        reference="The quick brown fox leaps over the dog",
        threshold=0.5,
    )
    assert res_high.score > 0.5
    assert res_high.passed is True

    res_low = await evaluator.evaluate(
        "Astrophysics studies celestial objects in deep space",
        reference="Baking sourdough bread requires flour and yeast",
    )
    assert res_low.score < 0.2
    assert res_low.passed is False


def test_percentile_and_aggregator() -> None:
    values = [10.0, 20.0, 30.0, 40.0, 50.0, 60.0, 70.0, 80.0, 90.0, 100.0]
    p50 = compute_percentile(values, 50.0)
    p95 = compute_percentile(values, 95.0)
    assert p50 == 55.0
    assert p95 == 95.5

    # Test aggregate_scorecard
    r1 = CaseResult(
        id="r1",
        evaluation_id="e1",
        case_id="c1",
        prompt="p1",
        passed=True,
        latency_ms=100.0,
    )
    r1.metrics = {"exact_match": {"score": 1.0}}
    r1.token_usage = {"prompt_tokens": 10, "completion_tokens": 20}

    r2 = CaseResult(
        id="r2",
        evaluation_id="e1",
        case_id="c2",
        prompt="p2",
        passed=False,
        latency_ms=200.0,
    )
    r2.metrics = {"exact_match": {"score": 0.0}}
    r2.token_usage = {"prompt_tokens": 15, "completion_tokens": 25}

    scorecard = aggregate_scorecard([r1, r2])
    assert scorecard.total_cases == 2
    assert scorecard.passed_cases == 1
    assert scorecard.failed_cases == 1
    assert scorecard.pass_rate == 0.5
    assert scorecard.avg_latency_ms == 150.0
    assert scorecard.total_prompt_tokens == 25
    assert scorecard.total_completion_tokens == 45
    assert scorecard.metric_averages["exact_match"] == 0.5
