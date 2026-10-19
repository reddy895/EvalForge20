"""Tests for benchmark runs, execution, and persistent evaluation history."""

from backend.app.main import app
from fastapi.testclient import TestClient

client = TestClient(app)


def test_list_benchmarks():
    """Verify available benchmark datasets are returned."""
    resp = client.get("/v1/benchmarks")
    assert resp.status_code == 200
    tasks = resp.json()
    assert len(tasks) >= 2
    assert any(t["task_id"] == "coding_basics" for t in tasks)


def test_run_mock_evaluation_and_persistence():
    """Verify end-to-end evaluation with deterministic mock, results retrieval and persistence."""
    # 1. Create and execute run
    run_payload = {
        "name": "Integration Test Suite",
        "model_identifier": "mock-model-v1",
        "provider": "mock",
        "task_id": "coding_basics",
        "max_cases": 2,
    }
    resp = client.post("/v1/evaluations", json=run_payload)
    assert resp.status_code == 201
    run_data = resp.json()
    run_id = run_data["id"]
    assert run_data["status"] == "completed"
    assert run_data["completed_cases"] == 2
    assert run_data["pass_rate"] == 1.0

    # 2. Retrieve history list
    list_resp = client.get("/v1/evaluations")
    assert list_resp.status_code == 200
    runs = list_resp.json()
    assert any(r["id"] == run_id for r in runs)

    # 3. Retrieve specific run detail
    detail_resp = client.get(f"/v1/evaluations/{run_id}")
    assert detail_resp.status_code == 200
    detail = detail_resp.json()
    assert len(detail["case_results"]) == 2
    assert detail["case_results"][0]["passed"] is True
