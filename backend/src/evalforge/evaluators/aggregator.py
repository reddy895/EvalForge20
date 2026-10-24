"""Composite metric aggregator and statistical scorecard calculator."""

import math

from pydantic import BaseModel, Field

from src.evalforge.storage.models.evaluation import CaseResult


class EvaluationScorecard(BaseModel):
    """Aggregate statistics and metric breakdown for an evaluation run."""

    total_cases: int
    completed_cases: int
    passed_cases: int
    failed_cases: int
    pass_rate: float
    avg_latency_ms: float | None = None
    median_latency_ms: float | None = None
    p50_latency_ms: float | None = None
    p95_latency_ms: float | None = None
    p99_latency_ms: float | None = None
    total_prompt_tokens: int | None = None
    total_completion_tokens: int | None = None
    avg_throughput_tok_s: float | None = None
    avg_tokens_per_second: float | None = None
    avg_load_duration_ms: float | None = None
    error_count: int = 0
    timeout_count: int = 0
    error_categories: dict[str, int] = Field(default_factory=dict)
    metric_averages: dict[str, float] = Field(default_factory=dict)


def compute_percentile(values: list[float], percentile: float) -> float:
    """Calculate percentile from a sorted list of float values."""
    if not values:
        return 0.0
    sorted_v = sorted(values)
    k = (len(sorted_v) - 1) * (percentile / 100.0)
    f = math.floor(k)
    c = math.ceil(k)
    if f == c:
        return round(sorted_v[int(k)], 2)
    d0 = sorted_v[int(f)] * (c - k)
    d1 = sorted_v[int(c)] * (k - f)
    return round(d0 + d1, 2)


def aggregate_scorecard(results: list[CaseResult]) -> EvaluationScorecard:
    """Compute aggregate pass rates, latency distributions, and metric averages."""
    total = len(results)
    if total == 0:
        return EvaluationScorecard(
            total_cases=0,
            completed_cases=0,
            passed_cases=0,
            failed_cases=0,
            pass_rate=0.0,
            avg_latency_ms=0.0,
            p50_latency_ms=0.0,
            p95_latency_ms=0.0,
            p99_latency_ms=0.0,
        )

    passed_count = sum(1 for r in results if r.passed)
    failed_count = total - passed_count
    pass_rate = round(passed_count / total, 4)

    # Reliability and error tracking
    error_count = 0
    timeout_count = 0
    error_categories: dict[str, int] = {}
    for r in results:
        err = getattr(r, "error_message", None)
        if err:
            error_count += 1
            err_lower = err.lower()
            if "timeout" in err_lower or "timed out" in err_lower:
                timeout_count += 1
                cat = "timeout"
            elif any(w in err_lower for w in ("connect", "unreachable", "refused")):
                cat = "connection_error"
            elif any(w in err_lower for w in ("not found", "404")):
                cat = "model_not_found"
            elif any(w in err_lower for w in ("json", "schema")):
                cat = "schema_validation_error"
            else:
                cat = "inference_error"
            error_categories[cat] = error_categories.get(cat, 0) + 1

    # Filter out artificial 0ms from failed cases if valid runs exist
    valid_latencies = [
        r.latency_ms
        for r in results
        if r.latency_ms is not None and not (getattr(r, "error_message", None) and r.latency_ms <= 0) and r.latency_ms > 0
    ]
    if valid_latencies:
        avg_latency = round(sum(valid_latencies) / len(valid_latencies), 2)
        p50 = compute_percentile(valid_latencies, 50.0)
        p95 = compute_percentile(valid_latencies, 95.0)
        p99 = compute_percentile(valid_latencies, 99.0)
    else:
        avg_latency = None
        p50 = None
        p95 = None
        p99 = None

    # Token aggregation
    prompt_tokens_list: list[int] = []
    comp_tokens_list: list[int] = []
    for r in results:
        usage = r.token_usage
        if usage:
            if usage.get("prompt_tokens") is not None:
                prompt_tokens_list.append(int(usage["prompt_tokens"]))
            if usage.get("completion_tokens") is not None:
                comp_tokens_list.append(int(usage["completion_tokens"]))

    tot_prompt = sum(prompt_tokens_list) if prompt_tokens_list else None
    tot_comp = sum(comp_tokens_list) if comp_tokens_list else None

    # Calculate average throughput
    avg_throughput: float | None = None
    if tot_comp and valid_latencies and sum(valid_latencies) > 0:
        avg_throughput = round(tot_comp / (sum(valid_latencies) / 1000.0), 2)

    # Calculate accurate tokens-per-second and load durations when reported
    tps_list = [
        float(r.token_usage["tokens_per_second"])
        for r in results
        if r.token_usage and r.token_usage.get("tokens_per_second") is not None
    ]
    avg_tps = round(sum(tps_list) / len(tps_list), 2) if tps_list else avg_throughput

    load_list = [
        float(r.token_usage["load_duration_ms"])
        for r in results
        if r.token_usage and r.token_usage.get("load_duration_ms") is not None
    ]
    avg_load = round(sum(load_list) / len(load_list), 2) if load_list else None

    # Per-metric averages
    metric_sums: dict[str, float] = {}
    metric_counts: dict[str, int] = {}
    for r in results:
        metrics = r.metrics
        for m_name, m_data in metrics.items():
            if m_name.startswith("_"):
                continue
            score = None
            if isinstance(m_data, dict) and "score" in m_data:
                score = m_data["score"]
            elif isinstance(m_data, (int, float)):
                score = float(m_data)

            if score is not None:
                metric_sums[m_name] = metric_sums.get(m_name, 0.0) + score
                metric_counts[m_name] = metric_counts.get(m_name, 0) + 1

    metric_averages = {m: round(metric_sums[m] / metric_counts[m], 4) for m in metric_sums}

    return EvaluationScorecard(
        total_cases=total,
        completed_cases=total,
        passed_cases=passed_count,
        failed_cases=failed_count,
        pass_rate=pass_rate,
        avg_latency_ms=avg_latency,
        median_latency_ms=p50,
        p50_latency_ms=p50,
        p95_latency_ms=p95,
        p99_latency_ms=p99,
        total_prompt_tokens=tot_prompt,
        total_completion_tokens=tot_comp,
        avg_throughput_tok_s=avg_throughput,
        avg_tokens_per_second=avg_tps,
        avg_load_duration_ms=avg_load,
        error_count=error_count,
        timeout_count=timeout_count,
        error_categories=error_categories,
        metric_averages=metric_averages,
    )
