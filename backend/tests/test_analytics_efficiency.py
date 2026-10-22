"""Unit tests for efficiency metrics and latency percentiles."""

from src.evalforge.analytics.efficiency import calculate_efficiency_metrics

def test_efficiency_empty() -> None:
    eff = calculate_efficiency_metrics([])
    assert eff.sample_count == 0
    assert eff.median_latency_ms == 0.0

def test_efficiency_percentiles_and_tps() -> None:
    latencies = [100.0, 150.0, 200.0, 250.0, 300.0]
    tokens = [20, 30, 40, 50, 60]  # Total 200 tokens, total 1.0 sec -> 200 tps
    eff = calculate_efficiency_metrics(latencies, tokens)
    assert eff.sample_count == 5
    assert eff.median_latency_ms == 200.0
    assert eff.total_tokens_generated == 200
    assert eff.avg_tokens_per_second == 200.0
