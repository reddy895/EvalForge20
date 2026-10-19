"""End-to-end integration tests verifying clean EvalForge20 architecture."""

from backend.app.main import app
from fastapi.testclient import TestClient

client = TestClient(app)


def test_health_check():
    """Verify backend health endpoint is active and returns version."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["app"] == "EvalForge20"


def test_model_catalog_search_and_filter():
    """Verify searching and filtering models across providers."""
    # List all
    res = client.get("/v1/models")
    assert res.status_code == 200
    models = res.json()
    assert len(models) >= 9

    # Filter local
    res_local = client.get("/v1/models?is_local=true")
    assert res_local.status_code == 200
    local_models = res_local.json()
    assert all(m["is_local"] for m in local_models)

    # Search by query
    res_qwen = client.get("/v1/models?query=qwen")
    assert res_qwen.status_code == 200
    qwen_models = res_qwen.json()
    assert any("qwen" in m["name"].lower() for m in qwen_models)


def test_model_profile_details():
    """Verify comprehensive model profile has hardware specs, benchmarks, and strengths."""
    res = client.get("/v1/models/llama-3.1-8b-instruct")
    assert res.status_code == 200
    profile = res.json()
    assert profile["provider"] == "Meta AI"
    assert profile["hardware"]["min_ram_gb"] >= 8
    assert len(profile["benchmarks"]) >= 3
    assert len(profile["strengths"]) > 0


def test_task_suitability_recommendation_engine():
    """Verify transparent recommendations for coding with hardware constraints."""
    res = client.post(
        "/v1/recommendations/task",
        json={"task": "coding", "prefer_local": True, "max_ram_gb": 16},
    )
    assert res.status_code == 200
    data = res.json()
    assert "recommendations" in data
    assert len(data["recommendations"]) > 0
    first = data["recommendations"][0]
    assert "match_score" in first
    assert "key_evidence" in first
    assert "hardware_fit" in first


def test_model_comparison_matrix():
    """Verify side-by-side comparison across 2 models."""
    res = client.post(
        "/v1/comparisons",
        json={"model_ids": ["llama-3.1-8b-instruct", "qwen-2.5-7b-instruct"]},
    )
    assert res.status_code == 200
    data = res.json()
    assert len(data["compared_models"]) == 2
    assert len(data["matrix"]) > 5
    assert "summary_verdict" in data


def test_local_evaluation_flow():
    """Verify creating, executing, and persisting a benchmark evaluation."""
    res = client.post(
        "/v1/evaluations",
        json={
            "name": "Integration Test Run",
            "model_identifier": "deterministic-mock-v1",
            "provider": "mock",
            "task_id": "coding_basics",
            "max_cases": 2,
        },
    )
    assert res.status_code == 201
    run = res.json()
    assert run["status"] == "completed"
    assert run["aggregates"]["completed_cases"] == 2
    assert run["aggregates"]["pass_rate"] == 1.0

    # Retrieve from history
    res_list = client.get("/v1/evaluations")
    assert res_list.status_code == 200
    runs = res_list.json()
    assert any(r["id"] == run["id"] for r in runs)
