"""Tests verifying dedicated evaluation results endpoint and multi-model data mapping."""

import pytest
from fastapi.testclient import TestClient

from src.evalforge.main import app


def test_get_execution_results_from_evaluation_run() -> None:
    """Verify that /api/executions/{id}/results returns structured analytics from evaluation_runs."""
    with TestClient(app) as client:
        # First list evaluations to get an existing ID
        res = client.get("/api/evaluations?limit=1")
        assert res.status_code == 200
        items = res.json().get("items", [])
        if not items:
            pytest.skip("No evaluation runs in database to verify against.")

        eval_id = items[0]["id"]
        results_res = client.get(f"/api/executions/{eval_id}/results")
        assert results_res.status_code == 200
        data = results_res.json()

        assert "id" in data
        assert "models" in data
        assert "model_summaries" in data
        assert "case_results" in data
        assert "distribution" in data
        assert isinstance(data["models"], list)
        assert isinstance(data["model_summaries"], list)
        assert isinstance(data["case_results"], list)
        assert "passed" in data["distribution"]
        assert "failed" in data["distribution"]


def test_get_execution_results_from_experiment() -> None:
    """Verify that /api/executions/{id}/results resolves experiment-backed execution records."""
    with TestClient(app) as client:
        # Check an experiment execution id if present
        res = client.get("/api/experiments?limit=1")
        assert res.status_code == 200
        exps = res.json().get("experiments", [])
        if not exps:
            pytest.skip("No experiments in database to verify against.")

        exec_id = exps[0].get("execution_id") or exps[0]["id"]
        results_res = client.get(f"/api/executions/{exec_id}/results")
        assert results_res.status_code == 200
        data = results_res.json()

        assert data["id"] == exec_id
        assert len(data["models"]) >= 1
        assert len(data["model_summaries"]) >= 1
        assert "pass_rate" in data
        assert "avg_latency_ms" in data


def test_get_execution_results_not_found() -> None:
    """Verify 404 response when querying a non-existent execution ID."""
    with TestClient(app) as client:
        res = client.get("/api/executions/00000000-0000-0000-0000-000000000000/results")
        assert res.status_code == 404


def test_evaluation_modular_fallback_to_execution() -> None:
    """Verify that /api/evaluations/{id}/results falls back cleanly to execution results."""
    with TestClient(app) as client:
        res = client.get("/api/experiments?limit=1")
        assert res.status_code == 200
        exps = res.json().get("experiments", [])
        if not exps:
            pytest.skip("No experiments in database.")

        exec_id = exps[0].get("execution_id") or exps[0]["id"]
        res_eval = client.get(f"/api/evaluations/{exec_id}/results")
        assert res_eval.status_code == 200
        assert res_eval.json()["id"] == exec_id
