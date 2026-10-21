"""Unit and integration test suite for multi-model benchmark comparisons."""

import uuid
import pytest
from starlette.testclient import TestClient

from src.evalforge.benchmarks.statistics import compute_model_metrics
from src.evalforge.main import app
from src.evalforge.storage.models.evaluation import CaseResult


def test_compute_model_metrics_no_fabrication() -> None:
    res1 = CaseResult(
        id="c1",
        evaluation_id="e1",
        case_id="case-1",
        prompt="p1",
        passed=True,
        latency_ms=100.0,
    )
    res1.metrics = {"exact_match": {"score": 1.0}}
    res1.token_usage = {"prompt_tokens": 5, "completion_tokens": 10}

    res2 = CaseResult(
        id="c2",
        evaluation_id="e1",
        case_id="case-2",
        prompt="p2",
        passed=False,
        latency_ms=200.0,
    )
    res2.metrics = {"exact_match": {"score": 0.0}}
    # Missing token usage on case 2
    res2.token_usage = None

    metrics = compute_model_metrics(
        model_id="mock-llama-3.1-8b",
        provider="mock",
        evaluation_id="e1",
        results=[res1, res2],
    )

    assert metrics.model_id == "mock-llama-3.1-8b"
    assert metrics.total_cases == 2
    assert metrics.passed_cases == 1
    assert metrics.failed_cases == 1
    assert metrics.pass_rate == 0.5
    assert metrics.avg_latency_ms == 150.0
    assert metrics.p50_latency_ms > 0
    assert metrics.metric_breakdown["exact_match"] == 0.5


def test_benchmark_api_comparison_lifecycle() -> None:
    unique_suffix = uuid.uuid4().hex[:8]
    with TestClient(app) as client:
        # 1. Create dataset
        ds_res = client.post(
            "/api/v1/datasets",
            json={
                "name": f"Benchmark Suite {unique_suffix}",
                "description": "Cross-model comparison dataset",
                "cases": [
                    {
                        "prompt": "What is the speed of light in vacuum?",
                        "expected_output": "Mock response for: What is the speed of light in vacuum?",
                    },
                    {
                        "prompt": "What is the boiling point of water in Celsius?",
                        "expected_output": "Mock response for: What is the boiling point of water in Celsius?",
                    },
                ],
            },
        )
        assert ds_res.status_code == 201
        dataset_id = ds_res.json()["id"]

        # 2. Run multi-model comparison
        compare_payload = {
            "name": f"Speed & Temp Benchmark {unique_suffix}",
            "dataset_id": dataset_id,
            "models": ["mock-llama-3.1-8b", "mock-qwen-2.5-7b"],
            "provider": "mock",
            "config": {
                "metrics": ["exact_match", "token_f1"],
                "concurrency": 2,
            },
        }

        compare_res = client.post("/api/v1/benchmarks/compare", json=compare_payload)
        assert compare_res.status_code == 201
        data = compare_res.json()

        comparison_id = data["id"]
        assert len(data["models"]) == 2
        assert len(data["evaluation_ids"]) == 2
        assert len(data["matrix"]) == 2

        # Verify reproducibility metadata
        repro = data["reproducibility"]
        assert repro["dataset_id"] == dataset_id
        assert "dataset_snapshot_hash" in repro
        assert len(repro["dataset_snapshot_hash"]) == 64  # SHA-256
        assert repro["metrics_evaluated"] == ["exact_match", "token_f1"]

        # 3. Retrieve comparison by ID
        get_res = client.get(f"/api/v1/benchmarks/{comparison_id}")
        assert get_res.status_code == 200
        get_data = get_res.json()
        assert get_data["id"] == comparison_id
        assert len(get_data["matrix"]) == 2
        assert get_data["matrix"][0]["total_cases"] == 2
        assert get_data["matrix"][1]["total_cases"] == 2
