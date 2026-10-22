"""Platform overview KPI aggregation logic."""

from collections.abc import Sequence
from dataclasses import dataclass


@dataclass
class PlatformKPIs:
    total_runs: int
    completed_runs: int
    failed_runs: int
    overall_pass_rate: float
    reliability_rate: float
    avg_latency_ms: float
    total_cases_evaluated: int

def calculate_platform_kpis(
    completed_runs: int,
    failed_runs: int,
    running_runs: int = 0,
    case_results: Sequence[dict] | None = None,
) -> PlatformKPIs:
    total_runs = completed_runs + failed_runs + running_runs
    finished = completed_runs + failed_runs
    reliability = round((completed_runs / finished) * 100.0, 1) if finished > 0 else 100.0

    cases = case_results or []
    total_cases = len(cases)
    passed_cases = sum(1 for c in cases if c.get("passed", False))
    pass_rate = round((passed_cases / total_cases) * 100.0, 1) if total_cases > 0 else 0.0

    latencies = [c.get("latency_ms", 0) for c in cases if c.get("latency_ms", 0) > 0]
    avg_latency = round(sum(latencies) / len(latencies), 1) if latencies else 0.0

    return PlatformKPIs(
        total_runs=total_runs,
        completed_runs=completed_runs,
        failed_runs=failed_runs,
        overall_pass_rate=pass_rate,
        reliability_rate=reliability,
        avg_latency_ms=avg_latency,
        total_cases_evaluated=total_cases,
    )
