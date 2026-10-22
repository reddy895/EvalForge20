"""Unit tests for platform KPI calculations."""

from src.evalforge.analytics.kpis import calculate_platform_kpis

def test_calculate_platform_kpis_empty() -> None:
    kpi = calculate_platform_kpis(0, 0, 0, [])
    assert kpi.total_runs == 0
    assert kpi.reliability_rate == 100.0
    assert kpi.overall_pass_rate == 0.0

def test_calculate_platform_kpis_mixed() -> None:
    cases = [
        {"passed": True, "latency_ms": 100.0},
        {"passed": True, "latency_ms": 120.0},
        {"passed": False, "latency_ms": 200.0},
    ]
    kpi = calculate_platform_kpis(completed_runs=9, failed_runs=1, running_runs=0, case_results=cases)
    assert kpi.total_runs == 10
    assert kpi.reliability_rate == 90.0
    assert kpi.overall_pass_rate == 66.7
    assert kpi.avg_latency_ms == 140.0
