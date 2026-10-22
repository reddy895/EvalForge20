"""Latency percentile and token throughput analytics."""

import statistics
from dataclasses import dataclass
from typing import Sequence

@dataclass
class EfficiencyMetrics:
    sample_count: int
    median_latency_ms: float
    p95_latency_ms: float
    avg_tokens_per_second: float | None
    total_tokens_generated: int

def calculate_efficiency_metrics(
    latencies_ms: Sequence[float],
    token_counts: Sequence[int] | None = None,
) -> EfficiencyMetrics:
    valid_latencies = sorted([float(lat) for lat in latencies_ms if lat > 0])
    count = len(valid_latencies)

    if count == 0:
        return EfficiencyMetrics(
            sample_count=0,
            median_latency_ms=0.0,
            p95_latency_ms=0.0,
            avg_tokens_per_second=None,
            total_tokens_generated=0,
        )

    median_lat = round(statistics.median(valid_latencies), 1)

    # 95th percentile
    if count >= 20:
        p95_idx = int(0.95 * count) - 1
        p95_lat = round(valid_latencies[max(0, p95_idx)], 1)
    else:
        p95_lat = round(valid_latencies[-1], 1)

    tokens = token_counts or []
    total_tok = sum(tokens)

    # Average tokens per second calculation
    tps = None
    if tokens and sum(valid_latencies) > 0:
        total_sec = sum(valid_latencies) / 1000.0
        tps = round(total_tok / total_sec, 1)

    return EfficiencyMetrics(
        sample_count=count,
        median_latency_ms=median_lat,
        p95_latency_ms=p95_lat,
        avg_tokens_per_second=tps,
        total_tokens_generated=total_tok,
    )
