"""Unit tests for deterministic code evaluators, registry, and score aggregation."""

import pytest
from app.domain.contracts import EvaluatorInput
from app.domain.errors import EvaluatorError
from app.domain.models import EvaluationCase
from app.domain.results import CaseResult, MetricResult
from app.evaluators.code.exact_match import ExactMatchEvaluator
from app.evaluators.code.json_schema import JSONSchemaEvaluator
from app.evaluators.code.json_validity import JSONValidityEvaluator
from app.evaluators.code.normalized_match import NormalizedMatchEvaluator
from app.evaluators.code.task_assertions import TaskAssertionEvaluator
from app.evaluators.registry import registry
from app.evaluators.summary.aggregator import aggregate_results


@pytest.mark.asyncio
async def test_exact_match_evaluator():
    """Verify exact match evaluator logic and edge cases."""
    evaluator = ExactMatchEvaluator()

    # Perfect match
    case = EvaluationCase(id="1", input="hello", expected_output="world")
    res = await evaluator.evaluate(EvaluatorInput(case=case, actual_output="world"))
    assert res.score == 1.0
    assert res.passed is True

    # Mismatch
    res = await evaluator.evaluate(EvaluatorInput(case=case, actual_output="World"))
    assert res.score == 0.0
    assert res.passed is False

    # Missing expected output (should be skipped, not failed)
    case_no_ref = EvaluationCase(id="2", input="hello", expected_output=None)
    res = await evaluator.evaluate(EvaluatorInput(case=case_no_ref, actual_output="anything"))
    assert res.score is None
    assert res.passed is None
    assert "No expected_output" in (res.reason or "")

    # Missing actual output
    res = await evaluator.evaluate(EvaluatorInput(case=case, actual_output=None))
    assert res.score == 0.0
    assert res.passed is False


@pytest.mark.asyncio
async def test_normalized_match_evaluator():
    """Verify normalized matching with case, punctuation, and numeric normalization."""
    evaluator = NormalizedMatchEvaluator()

    case = EvaluationCase(id="1", input="question", expected_output="Paris!")
    res = await evaluator.evaluate(EvaluatorInput(case=case, actual_output="  paris  "))
    assert res.score == 1.0
    assert res.passed is True

    # Numeric normalization: 42.0 vs 42
    case_num = EvaluationCase(id="2", input="math", expected_output="42")
    res = await evaluator.evaluate(EvaluatorInput(case=case_num, actual_output="42.0"))
    assert res.score == 1.0
    assert res.passed is True


@pytest.mark.asyncio
async def test_json_validity_evaluator():
    """Verify JSON validity parser with markdown blocks and chatter."""
    evaluator = JSONValidityEvaluator()

    case = EvaluationCase(id="1", input="json test")

    # Plain JSON
    res = await evaluator.evaluate(EvaluatorInput(case=case, actual_output='{"status": "ok"}'))
    assert res.score == 1.0
    assert res.passed is True

    # Markdown fenced code block
    fenced = 'Here is the response:\n```json\n{\n  "status": "ok",\n  "count": 5\n}\n```\nHope that helps!'
    res = await evaluator.evaluate(EvaluatorInput(case=case, actual_output=fenced))
    assert res.score == 1.0
    assert res.passed is True

    # Malformed JSON
    res = await evaluator.evaluate(EvaluatorInput(case=case, actual_output="{bad json"))
    assert res.score == 0.0
    assert res.passed is False
    assert "Failed to parse JSON" in (res.reason or "")


@pytest.mark.asyncio
async def test_json_schema_evaluator():
    """Verify JSON Schema validation against structured output."""
    evaluator = JSONSchemaEvaluator()

    schema = {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "age": {"type": "integer", "minimum": 0},
        },
        "required": ["name", "age"],
    }
    case = EvaluationCase(id="1", input="user info", metadata={"schema": schema})

    # Valid instance
    res = await evaluator.evaluate(
        EvaluatorInput(case=case, actual_output='{"name": "Alice", "age": 30}')
    )
    assert res.score == 1.0
    assert res.passed is True

    # Invalid instance (age negative, violates schema constraint)
    res = await evaluator.evaluate(
        EvaluatorInput(case=case, actual_output='{"name": "Bob", "age": -5}')
    )
    assert res.score == 0.0
    assert res.passed is False
    assert "Schema violation" in (res.reason or "")

    # Missing schema (should skip gracefully)
    case_no_schema = EvaluationCase(id="2", input="user info")
    res = await evaluator.evaluate(
        EvaluatorInput(case=case_no_schema, actual_output='{"anything": 1}')
    )
    assert res.score is None
    assert res.passed is None


@pytest.mark.asyncio
async def test_task_assertions_evaluator():
    """Verify safe, declarative task assertion checks."""
    evaluator = TaskAssertionEvaluator()

    assertions = [
        {"name": "check_keywords", "type": "contains_all", "value": ["alpha", "beta"]},
        {"name": "check_no_forbidden", "type": "not_contains", "value": ["leak", "secret"]},
        {"name": "check_min_len", "type": "min_length", "value": 10},
    ]
    case = EvaluationCase(id="1", input="task", metadata={"assertions": assertions})

    # Passes all assertions
    valid_text = "The system contains alpha and beta with sufficient length"
    res = await evaluator.evaluate(EvaluatorInput(case=case, actual_output=valid_text))
    assert res.score == 1.0
    assert res.passed is True

    # Fails forbidden word check
    leaked_text = "The alpha beta contains a secret key"
    res = await evaluator.evaluate(EvaluatorInput(case=case, actual_output=leaked_text))
    assert res.score < 1.0
    assert res.passed is False


def test_evaluator_registry():
    """Verify discovery and lookup in EvaluatorRegistry."""
    exact = registry.get("exact_match")
    assert isinstance(exact, ExactMatchEvaluator)

    with pytest.raises(EvaluatorError) as exc_info:
        registry.get("non_existent_metric_id")
    assert "Unknown metric" in str(exc_info.value)
    assert "exact_match" in str(exc_info.value)


def test_aggregate_results_strict_denominators():
    """Verify metric aggregation preserves correct denominators and does not fabricate zeros."""
    res1 = CaseResult(
        case_id="c1",
        run_id="run1",
        input="q1",
        actual_output="ans1",
        metrics=[
            MetricResult(metric_id="exact_match", metric_name="Exact Match", score=1.0, passed=True)
        ],
        latency_ms=100.0,
        token_usage={"total_tokens": 50},
    )
    res2 = CaseResult(
        case_id="c2",
        run_id="run1",
        input="q2",
        actual_output="ans2",
        metrics=[
            MetricResult(
                metric_id="exact_match", metric_name="Exact Match", score=0.0, passed=False
            )
        ],
        latency_ms=200.0,
        token_usage=None,  # Provider did not report tokens
    )
    # Case with no reference output (score is None, passed is None)
    res3 = CaseResult(
        case_id="c3",
        run_id="run1",
        input="q3",
        actual_output="ans3",
        metrics=[
            MetricResult(
                metric_id="exact_match", metric_name="Exact Match", score=None, passed=None
            )
        ],
        latency_ms=150.0,
        token_usage=None,
    )

    agg = aggregate_results([res1, res2, res3], case_categories={"c1": "catA", "c2": "catA"})

    assert agg.total_cases == 3
    assert agg.completed_cases == 3
    assert agg.failed_cases == 0

    # Pass rate: only c1 and c2 were eligible. c1 passed, c2 failed -> 1 / 2 = 0.5
    assert agg.pass_rate == 0.5
    assert agg.metric_averages["exact_match"] == 0.5
    assert agg.metric_pass_rates["exact_match"] == 0.5

    # Latencies
    assert agg.mean_latency_ms == 150.0
    assert agg.median_latency_ms == 150.0
    assert agg.p95_latency_ms is not None

    # Total tokens measured: exactly 50 (not fabricated 0 for unmeasured cases)
    assert agg.total_tokens == 50
