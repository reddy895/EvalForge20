"""Composite metric aggregator and statistical scorecard calculator."""

import math
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from src.evalforge.storage.models.evaluation import CaseResult


class EvaluationScorecard(BaseModel):
    """Aggregate statistics and metric breakdown for an evaluation run."""

    total_cases: int
    completed_cases: int
    passed_cases: int
    failed_cases: int
    pass_rate: float
    avg_latency_ms: float
    p50_latency_ms: float
    p95_latency_ms: float
    p99_latency_ms: float
    total_prompt_tokens: Optional[int] = None
    total_completion_tokens: Optional[int] = None
    avg_throughput_tok_s: Optional[float] = None
    metric_averages: Dict[str, float] = Field(default_factory=dict)


def compute_percentile(values: List[float], percentile: float) -> float:
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


def aggregate_scorecard(results: List[CaseResult]) -> EvaluationScorecard:
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

    latencies = [r.latency_ms for r in results if r.latency_ms is not None]
    avg_latency = round(sum(latencies) / len(latencies), 2) if latencies else 0.0
    p50 = compute_percentile(latencies, 50.0)
    p95 = compute_percentile(latencies, 95.0)
    p99 = compute_percentile(latencies, 99.0)

    # Token aggregation
    prompt_tokens_list: List[int] = []
    comp_tokens_list: List[int] = []
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
    avg_throughput: Optional[float] = None
    if tot_comp and sum(latencies) > 0:
        avg_throughput = round(tot_comp / (sum(latencies) / 1000.0), 2)

    # Per-metric averages
    metric_sums: Dict[str, float] = {}
    metric_counts: Dict[str, int] = {}
    for r in results:
        metrics = r.metrics
        for m_name, m_data in metrics.items():
            score = None
            if isinstance(m_data, dict) and "score" in m_data:
                score = m_data["score"]
            elif isinstance(m_data, (int, float)):
                score = float(m_data)

            if score is not None:
                metric_sums[m_name] = metric_sums.get(m_name, 0.0) + score
                metric_counts[m_name] = metric_counts.get(m_name, 0) + 1

    metric_averages = {
        m: round(metric_sums[m] / metric_counts[m], 4) for m in metric_sums
    }

    return EvaluationScorecard(
        total_cases=total,
        completed_cases=total,
        passed_cases=passed_count,
        failed_cases=failed_count,
        pass_rate=pass_rate,
        avg_latency_ms=avg_latency,
        p50_latency_ms=p50,
        p95_latency_ms=p95,
        p99_latency_ms=p99,
        total_prompt_tokens=tot_prompt,
        total_completion_tokens=tot_comp,
        avg_throughput_tok_s=avg_throughput,
        metric_averages=metric_averages,
    )
