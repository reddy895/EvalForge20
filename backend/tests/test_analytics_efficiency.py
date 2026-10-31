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


def test_api_analytics_efficiency_contract_and_mock_filtering() -> None:
    from fastapi.testclient import TestClient
    from src.evalforge.main import app

    with TestClient(app) as client:
        # Default: include_mock=False
        resp = client.get("/api/v1/analytics/efficiency")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)

        # No mock models should be present in the default filtered telemetry
        for item in data:
            assert not str(item["model_id"]).startswith("mock-")
            assert "model_name" in item
            assert "tokens_per_second" in item
            assert "avg_latency_ms" in item
            assert "efficiency_score" in item
            if item.get("tokens_per_second") and item.get("avg_latency_ms"):
                assert item["efficiency_score"] is not None
                assert item["efficiency_score"] >= 0.0

        # Query param include_mock=true
        resp_mock = client.get("/api/v1/analytics/efficiency?include_mock=true")
        assert resp_mock.status_code == 200
        data_mock = resp_mock.json()
        assert isinstance(data_mock, list)
        assert len(data_mock) >= len(data)
