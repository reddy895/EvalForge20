"""Platform End-to-End Regression Tests.

Validates backend startup health contract, decoupling of API readiness from provider reachability,
and robust handling of evaluation endpoints under varied provider states.
"""

import pytest
from starlette.testclient import TestClient
from src.evalforge.main import app


def test_api_readiness_endpoint() -> None:
    """GET /health must return HTTP 200 indicating FastAPI application is ready."""
    with TestClient(app) as client:
        res = client.get("/health")
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "healthy"
        assert "EvalForge20" in data["app"]
        assert data["api_ready"] is True
        assert data["database_connected"] is True


def test_ollama_provider_health_decoupling() -> None:
    """GET /health/ready reports API server readiness separately from external provider reachability."""
    with TestClient(app) as client:
        res = client.get("/health/ready")
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "ready"
        assert data["api_ready"] is True
        assert "providers_online" in data
        assert "ollama" in data["providers_online"]


def test_provider_models_endpoint_contract() -> None:
    """GET /api/v1/models returns registered models and indicates readiness."""
    with TestClient(app) as client:
        res = client.get("/api/v1/models")
        assert res.status_code == 200
        data = res.json()
        assert "models" in data
        models = data["models"]
        assert isinstance(models, list)
        assert len(models) > 0
        for m in models:
            assert "id" in m
            assert "name" in m
            assert "provider" in m


def test_end_to_end_evaluation_execution() -> None:
    """Full lifecycle: create dataset -> trigger evaluation -> poll completion -> verify case results persistence."""
    import time
    with TestClient(app) as client:
        # 1. Create evaluation benchmark dataset
        ds_payload = {
            "name": f"E2E Benchmark Suite {time.time()}",
            "description": "Automated end-to-end evaluation suite",
            "cases": [
                {
                    "prompt": "Evaluate deterministic output A",
                    "expected_output": "Output A",
                    "assertion_type": "exact_match",
                },
                {
                    "prompt": "Evaluate deterministic output B",
                    "expected_output": "Output B",
                    "assertion_type": "exact_match",
                },
            ],
        }
        ds_res = client.post("/api/v1/datasets", json=ds_payload)
        assert ds_res.status_code == 201
        dataset_id = ds_res.json()["id"]

        # 2. Trigger evaluation run
        eval_payload = {
            "name": f"E2E Test Run {time.time()}",
            "model_id": "mock-llama-3.1-8b",
            "provider": "mock",
            "dataset_id": dataset_id,
            "metrics": ["exact_match"],
        }
        eval_res = client.post("/api/v1/evaluations", json=eval_payload)
        assert eval_res.status_code == 201
        run_data = eval_res.json()
        run_id = run_data["id"]
        assert run_data["status"] in ("queued", "pending", "running", "completed")

        # 3. Poll until evaluation job completes
        final_run = None
        for _ in range(60):
            time.sleep(0.05)
            poll_res = client.get(f"/api/v1/evaluations/{run_id}")
            assert poll_res.status_code == 200
            final_run = poll_res.json()
            if final_run["status"] in ("completed", "completed_with_errors", "failed"):
                break

        assert final_run is not None
        assert final_run["status"] in ("completed", "completed_with_errors")
        assert final_run["total_cases"] == 2

        # 4. Fetch detailed case audit records
        detail_res = client.get(f"/api/v1/evaluations/{run_id}/results")
        assert detail_res.status_code == 200
        res_data = detail_res.json()
        case_records = res_data.get("case_results") or res_data.get("results")
        assert isinstance(case_records, list)
        assert len(case_records) == 2
        for case in case_records:
            assert "prompt" in case
            assert "expected_output" in case
            assert "passed" in case
