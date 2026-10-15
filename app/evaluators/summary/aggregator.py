"""Metric aggregation with strict denominator tracking and missing-value differentiation."""

import math
import statistics
from typing import Any

from app.domain.results import AggregateMetrics, CaseResult


def calculate_percentile(values: list[float], percentile: float) -> float | None:
    """Calculate the p-th percentile from a list of sorted values using linear interpolation."""
    if not values:
        return None
    if len(values) == 1:
        return values[0]
    sorted_v = sorted(values)
    k = (len(sorted_v) - 1) * (percentile / 100.0)
    f = math.floor(k)
    c = math.ceil(k)
    if f == c:
        return sorted_v[int(k)]
    d0 = sorted_v[int(f)] * (c - k)
    d1 = sorted_v[int(c)] * (k - f)
    return d0 + d1


def aggregate_results(
    case_results: list[CaseResult],
    case_categories: dict[str, str | None] | None = None,
) -> AggregateMetrics:
    """Aggregate per-case results into dataset-level metrics with accurate denominators.

    Clearly distinguishes between:
    - 0 values vs unavailable/unmeasured values (represented as None).
    - Failed cases vs skipped cases.
    - Eligible cases for each specific metric denominator.
    """
    total_cases = len(case_results)
    completed_cases = 0
    failed_cases = 0

    metric_scores: dict[str, list[float]] = {}
    metric_pass_flags: dict[str, list[bool]] = {}
    valid_latencies: list[float] = []
    token_counts: list[int] = []
    error_counts: dict[str, int] = {}

    overall_case_passed_flags: list[bool] = []
    category_case_results: dict[str, list[bool]] = {}

    for res in case_results:
        # Check execution status
        if res.error_category is not None or res.actual_output is None:
            failed_cases += 1
            cat_name = res.error_category or "unknown_error"
            error_counts[cat_name] = error_counts.get(cat_name, 0) + 1
        else:
            completed_cases += 1

        # Track latency
        if res.latency_ms is not None and res.latency_ms >= 0:
            valid_latencies.append(res.latency_ms)

        # Track tokens (do not assume 0 if missing)
        if res.token_usage and "total_tokens" in res.token_usage:
            token_counts.append(res.token_usage["total_tokens"])

        # Track metrics
        case_has_evaluated_metric = False
        case_all_metrics_passed = True

        for m in res.metrics:
            if m.score is not None:
                metric_scores.setdefault(m.metric_id, []).append(m.score)
            if m.passed is not None:
                case_has_evaluated_metric = True
                metric_pass_flags.setdefault(m.metric_id, []).append(m.passed)
                if not m.passed:
                    case_all_metrics_passed = False

        if case_has_evaluated_metric:
            overall_case_passed_flags.append(case_all_metrics_passed)

            # Track category performance
            case_cat = (case_categories or {}).get(res.case_id)
            if case_cat:
                category_case_results.setdefault(case_cat, []).append(case_all_metrics_passed)

    # Compute overall pass rate using only eligible cases
    pass_rate: float | None = None
    if overall_case_passed_flags:
        pass_rate = round(
            sum(1 for p in overall_case_passed_flags if p) / len(overall_case_passed_flags), 4
        )

    # Compute per-metric averages
    metric_averages: dict[str, float] = {}
    for mid, scores in metric_scores.items():
        if scores:
            metric_averages[mid] = round(sum(scores) / len(scores), 4)

    # Compute per-metric pass rates
    metric_pass_rates: dict[str, float] = {}
    for mid, flags in metric_pass_flags.items():
        if flags:
            metric_pass_rates[mid] = round(sum(1 for f in flags if f) / len(flags), 4)

    # Latency statistics
    mean_latency: float | None = None
    median_latency: float | None = None
    p95_latency: float | None = None

    if valid_latencies:
        mean_latency = round(statistics.fmean(valid_latencies), 2)
        median_latency = round(statistics.median(valid_latencies), 2)
        if len(valid_latencies) >= 2:
            p95 = calculate_percentile(valid_latencies, 95.0)
            p95_latency = round(p95, 2) if p95 is not None else None

    # Total tokens (None if no provider reported tokens)
    total_tokens = sum(token_counts) if token_counts else None

    # Category performance
    category_performance: dict[str, dict[str, float]] = {}
    for cat_name, flags in category_case_results.items():
        if flags:
            c_rate = sum(1 for f in flags if f) / len(flags)
            category_performance[cat_name] = {
                "pass_rate": round(c_rate, 4),
                "total_cases": float(len(flags)),
            }

    return AggregateMetrics(
        total_cases=total_cases,
        completed_cases=completed_cases,
        failed_cases=failed_cases,
        pass_rate=pass_rate,
        mean_latency_ms=mean_latency,
        median_latency_ms=median_latency,
        p95_latency_ms=p95_latency,
        total_tokens=total_tokens,
        metric_averages=metric_averages,
        metric_pass_rates=metric_pass_rates,
        category_performance=category_performance,
        error_distribution=error_counts,
    )
