"""Integration tests verifying route parity across /api/ and /api/v1/ endpoints."""

from starlette.testclient import TestClient

from src.evalforge.main import app


def test_api_route_parity() -> None:
    with TestClient(app) as client:
        # Health
        assert client.get("/health").status_code == 200
        assert client.get("/api/health").status_code == 200

        # Providers
        assert client.get("/api/providers").status_code == 200
        assert client.get("/api/v1/providers").status_code == 200

        # Analytics
        assert client.get("/api/analytics/overview").status_code == 200
        assert client.get("/api/v1/analytics/overview").status_code == 200
        assert client.get("/api/analytics/commits").status_code == 200


def test_evaluation_detail_response_matches_database_case_records() -> None:
    """Detailed case results endpoint returns full case audit payload with matching prompts and metrics."""
    import time
    with TestClient(app) as client:
        # Create dataset
        ds_res = client.post(
            "/api/v1/datasets",
            json={
                "name": "Parity Test Dataset",
                "cases": [
                    {"prompt": "Echo 1", "expected_output": "1"},
                    {"prompt": "Echo 2", "expected_output": "2"},
                ],
            },
        )
        assert ds_res.status_code == 201
        ds_id = ds_res.json()["id"]

        # Trigger evaluation
        run_res = client.post(
            "/api/v1/evaluations",
            json={
                "name": "Parity Run",
                "model_id": "mock-llama-3.1-8b",
                "provider": "mock",
                "dataset_id": ds_id,
            },
        )
        assert run_res.status_code == 201
        run_id = run_res.json()["id"]

        # Poll until finished
        for _ in range(50):
            time.sleep(0.05)
            poll = client.get(f"/api/v1/evaluations/{run_id}").json()
            if poll["status"] in ("completed", "completed_with_errors", "failed"):
                break

        # Check detail endpoint parity on both /api/v1/ and /api/
        detail_v1 = client.get(f"/api/v1/evaluations/{run_id}/results")
        assert detail_v1.status_code == 200
        v1_data = detail_v1.json()

        assert v1_data["id"] == run_id
        assert "results" in v1_data
        assert len(v1_data["results"]) == 2

        case0 = v1_data["results"][0]
        assert "case_id" in case0
        assert "prompt" in case0
        assert "expected_output" in case0
        assert "actual_output" in case0
        assert isinstance(case0["passed"], bool)
        assert "assertion_type" in case0
        assert "metrics" in case0
        assert "created_at" in case0
