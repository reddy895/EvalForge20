"""Integration tests for FastAPI REST endpoints and Typer CLI workflows."""

from pathlib import Path

from app.cli.main import cli_app
from app.main import app
from fastapi.testclient import TestClient
from typer.testing import CliRunner

client = TestClient(app)
runner = CliRunner()


def test_api_health_and_ready():
    """Verify health and readiness probes."""
    resp_health = client.get("/health")
    assert resp_health.status_code == 200
    data_health = resp_health.json()
    assert data_health["status"] == "ok"
    assert "version" in data_health

    resp_ready = client.get("/ready")
    assert resp_ready.status_code == 200
    data_ready = resp_ready.json()
    assert data_ready["status"] == "ready"
    assert data_ready["database"] == "connected"
    assert "mock" in data_ready["available_providers"]


def test_api_providers_and_metrics_discovery():
    """Verify provider and evaluator discovery endpoints."""
    resp_p = client.get("/v1/providers")
    assert resp_p.status_code == 200
    providers = resp_p.json()
    assert "mock" in providers
    assert "ollama" in providers

    resp_m = client.get("/v1/metrics")
    assert resp_m.status_code == 200
    metrics = resp_m.json()
    metric_ids = [m["metric_id"] for m in metrics]
    assert "exact_match" in metric_ids
    assert "normalized_match" in metric_ids
    assert "json_validity" in metric_ids


def test_api_dataset_validate_endpoint():
    """Verify dataset validation endpoint."""
    raw_content = (
        '{"id":"case-1","input":"What is 2+2?","expected_output":"4"}\n'
        '{"id":"case-2","input":"What is 3+3?","expected_output":"6"}\n'
    )
    resp = client.post("/v1/datasets/validate", json={"content": raw_content})
    assert resp.status_code == 200
    report = resp.json()
    assert report["is_valid"] is True
    assert report["valid_cases_count"] == 2


def test_api_evaluation_lifecycle_and_report():
    """Verify complete evaluation execution, results retrieval, and report export via API."""
    payload = {
        "name": "API Integration Run",
        "dataset_path": "examples/datasets/basic.jsonl",
        "target": {
            "target_name": "mock-test",
            "target_type": "mock",
            "provider_name": "mock",
            "model_identifier": "mock-model-v1",
        },
        "evaluators": [
            {"evaluator_name": "Exact Match", "metric_id": "exact_match"},
        ],
    }
    resp = client.post("/v1/evaluations", json=payload)
    assert resp.status_code == 201
    summary = resp.json()
    run_id = summary["run_id"]
    assert summary["status"] == "completed"
    assert summary["total_cases"] == 4

    # 1. List runs
    resp_list = client.get("/v1/evaluations")
    assert resp_list.status_code == 200
    runs = resp_list.json()
    assert any(r["run_id"] == run_id for r in runs)

    # 2. Get specific run
    resp_get = client.get(f"/v1/evaluations/{run_id}")
    assert resp_get.status_code == 200
    details = resp_get.json()
    assert details["run"]["run_id"] == run_id
    assert details["aggregates"] is not None

    # 3. Get per-case results
    resp_cases = client.get(f"/v1/evaluations/{run_id}/results?limit=10&offset=0")
    assert resp_cases.status_code == 200
    cases = resp_cases.json()
    assert len(cases) == 4

    # 4. Get report JSON
    resp_report = client.get(f"/v1/reports/{run_id}")
    assert resp_report.status_code == 200
    report = resp_report.json()
    assert report["report_schema_version"] == "1.0.0"
    assert report["run_id"] == run_id

    # 5. Get failed cases
    resp_failures = client.get(f"/v1/evaluations/{run_id}/failures")
    assert resp_failures.status_code == 200
    assert isinstance(resp_failures.json(), list)

    # 6. Delete evaluation run
    resp_del = client.delete(f"/v1/evaluations/{run_id}")
    assert resp_del.status_code == 200
    assert "deleted successfully" in resp_del.json()["message"]

    # Verify 404 on deleted run
    resp_gone = client.get(f"/v1/evaluations/{run_id}")
    assert resp_gone.status_code == 404


def test_api_validation_error_handler():
    """Verify structured 422 error response on invalid request schema."""
    resp = client.post("/v1/evaluations", json={"bad_field": 123})
    assert resp.status_code == 422
    err_body = resp.json()
    assert err_body["error"] == "RequestValidationError"
    assert "validation_errors" in err_body["details"]


def test_cli_provider_and_evaluation_workflow(tmp_path: Path):
    """Verify CLI commands for providers, running evaluations, and exporting reports."""
    # 1. Provider list & check
    res_list = runner.invoke(cli_app, ["provider", "list"])
    assert res_list.exit_code == 0
    assert "mock" in res_list.stdout

    res_check = runner.invoke(cli_app, ["provider", "check", "mock"])
    assert res_check.exit_code == 0
    assert "is healthy" in res_check.stdout

    # 2. Run evaluation
    res_eval = runner.invoke(
        cli_app,
        [
            "evaluate",
            "--dataset",
            "examples/datasets/basic.jsonl",
            "--provider",
            "mock",
            "--name",
            "CLI Workflow Test",
        ],
    )
    assert res_eval.exit_code == 0
    assert "Run Finished: [COMPLETED]" in res_eval.stdout

    # 3. Runs list
    res_runs = runner.invoke(cli_app, ["runs", "list"])
    assert res_runs.exit_code == 0
    assert "CLI Workflow Test" in res_runs.stdout

    # Extract run ID from runs list table
    lines = res_runs.stdout.splitlines()
    run_id = None
    for line in lines:
        if "CLI Workflow Test" in line:
            parts = [p.strip() for p in line.split("│") if p.strip()]
            if parts:
                run_id = parts[0]
                break

    assert run_id is not None

    # 4. Export report via CLI
    report_file = tmp_path / "cli_report.json"
    res_export = runner.invoke(
        cli_app, ["report", "export", run_id, "--format", "json", "--output", str(report_file)]
    )
    assert res_export.exit_code == 0
    assert report_file.exists()
