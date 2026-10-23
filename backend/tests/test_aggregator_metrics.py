"""Unit tests for the metrics aggregator — percentile calculations, scorecard accuracy, and token stats."""

from types import SimpleNamespace

import pytest

from src.evalforge.evaluators.aggregator import (
    aggregate_scorecard,
    compute_percentile,
)


# ---------------------------------------------------------------------------
# Percentile helper tests
# ---------------------------------------------------------------------------

class TestComputePercentile:
    def test_empty_list_returns_zero(self) -> None:
        assert compute_percentile([], 50) == 0.0

    def test_single_value(self) -> None:
        assert compute_percentile([42.0], 50) == 42.0
        assert compute_percentile([42.0], 95) == 42.0
        assert compute_percentile([42.0], 99) == 42.0

    def test_even_list_median(self) -> None:
        result = compute_percentile([100.0, 200.0, 300.0, 400.0], 50)
        assert result == 250.0

    def test_p95_correctness(self) -> None:
        # 20 values: 10..200 in steps of 10
        values = [float(i * 10) for i in range(1, 21)]
        p95 = compute_percentile(values, 95)
        # P95 of 20 values should be close to 195
        assert 180.0 <= p95 <= 200.0

    def test_ascending_percentiles(self) -> None:
        values = [float(i) for i in range(1, 101)]
        p50 = compute_percentile(values, 50)
        p95 = compute_percentile(values, 95)
        p99 = compute_percentile(values, 99)
        assert p50 < p95 < p99

    def test_identical_values(self) -> None:
        values = [150.0] * 10
        assert compute_percentile(values, 50) == 150.0
        assert compute_percentile(values, 95) == 150.0


# ---------------------------------------------------------------------------
# Fake CaseResult factory (avoids SQLAlchemy ORM instrumentation)
# ---------------------------------------------------------------------------

def _make_case(
    passed: bool,
    latency_ms: float,
    token_usage: dict | None = None,
    metrics: dict | None = None,
) -> SimpleNamespace:
    """Create a lightweight fake CaseResult for unit-testing the aggregator."""
    return SimpleNamespace(
        passed=passed,
        latency_ms=latency_ms,
        token_usage=token_usage or {},
        metrics=metrics or {},
    )


# ---------------------------------------------------------------------------
# Scorecard aggregation tests
# ---------------------------------------------------------------------------

class TestAggregateScorecard:
    def test_empty_results_returns_zero_scorecard(self) -> None:
        sc = aggregate_scorecard([])
        assert sc.total_cases == 0
        assert sc.pass_rate == 0.0
        assert sc.avg_latency_ms == 0.0
        assert sc.p95_latency_ms == 0.0

    def test_all_pass(self) -> None:
        cases = [_make_case(True, 100.0), _make_case(True, 200.0)]
        sc = aggregate_scorecard(cases)
        assert sc.total_cases == 2
        assert sc.passed_cases == 2
        assert sc.failed_cases == 0
        assert sc.pass_rate == 1.0

    def test_all_fail(self) -> None:
        cases = [_make_case(False, 50.0), _make_case(False, 75.0)]
        sc = aggregate_scorecard(cases)
        assert sc.passed_cases == 0
        assert sc.failed_cases == 2
        assert sc.pass_rate == 0.0

    def test_mixed_pass_rate(self) -> None:
        cases = [_make_case(True, 100.0), _make_case(False, 200.0)]
        sc = aggregate_scorecard(cases)
        assert sc.pass_rate == 0.5
        assert sc.passed_cases == 1
        assert sc.failed_cases == 1

    def test_avg_latency_calculation(self) -> None:
        cases = [_make_case(True, 100.0), _make_case(True, 300.0)]
        sc = aggregate_scorecard(cases)
        assert sc.avg_latency_ms == 200.0

    def test_p95_latency_over_many_cases(self) -> None:
        cases = [_make_case(True, float(i)) for i in range(1, 101)]
        sc = aggregate_scorecard(cases)
        # P95 of 1..100 should be close to 95
        assert sc.p95_latency_ms >= 90.0

    def test_token_usage_aggregation(self) -> None:
        usage = {"prompt_tokens": 50, "completion_tokens": 30}
        cases = [_make_case(True, 100.0, token_usage=usage)] * 3
        sc = aggregate_scorecard(cases)
        assert sc.total_prompt_tokens == 150
        assert sc.total_completion_tokens == 90

    def test_tokens_per_second_from_ollama_telemetry(self) -> None:
        usage = {
            "tokens_per_second": 45.5,
            "load_duration_ms": 120.0,
            "prompt_tokens": 10,
            "completion_tokens": 20,
        }
        cases = [_make_case(True, 200.0, token_usage=usage)] * 4
        sc = aggregate_scorecard(cases)
        assert sc.avg_tokens_per_second == pytest.approx(45.5, 0.01)
        assert sc.avg_load_duration_ms == pytest.approx(120.0, 0.01)

    def test_metric_averages_computed_correctly(self) -> None:
        m1 = {"exact_match": {"score": 1.0}}
        m2 = {"exact_match": {"score": 0.0}}
        cases = [_make_case(True, 100.0, metrics=m1), _make_case(False, 100.0, metrics=m2)]
        sc = aggregate_scorecard(cases)
        assert "exact_match" in sc.metric_averages
        assert sc.metric_averages["exact_match"] == pytest.approx(0.5, 0.001)

    def test_metric_averages_private_keys_excluded(self) -> None:
        m = {"_internal": {"score": 0.9}, "bleu": {"score": 0.8}}
        cases = [_make_case(True, 100.0, metrics=m)]
        sc = aggregate_scorecard(cases)
        assert "_internal" not in sc.metric_averages
        assert "bleu" in sc.metric_averages

    def test_median_equals_p50(self) -> None:
        cases = [_make_case(True, float(i * 10)) for i in range(1, 11)]
        sc = aggregate_scorecard(cases)
        assert sc.median_latency_ms == sc.p50_latency_ms
