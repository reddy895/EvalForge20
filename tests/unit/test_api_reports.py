"""Unit tests for multi-format evaluation report API endpoint."""

import pytest
from app.domain.models import TargetConfiguration, TargetType
from app.domain.results import AggregateMetrics, CaseResult, MetricResult
from app.domain.state import EvaluationRunStatus
from app.main import app
from app.runner.config import EvaluationRunConfig, EvaluationRunRecord
from app.storage.database import get_db
from app.storage.repositories import EvaluationRepository
from fastapi.testclient import TestClient


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def test_get_report_multi_formats(client: TestClient):
    """Verify /v1/reports/{run_id} returns JSON, Markdown, and CSV appropriately."""
    db = next(get_db())
    repo = EvaluationRepository(db)

    run_id = "run_api_report_test_1"
    record = EvaluationRunRecord(
        run_id=run_id,
        name="Multi-Format API Report Test",
        status=EvaluationRunStatus.COMPLETED,
        config=EvaluationRunConfig(
            run_id=run_id,
            target=TargetConfiguration(
                target_name="Qwen Target",
                target_type=TargetType.OLLAMA,
                provider_name="ollama",
                model_identifier="qwen2.5:3b",
            ),
        ),
        total_cases=1,
        completed_cases=1,
        failed_cases=0,
    )
    repo.create_run(record)
    repo.update_run_completion(
        run_id=run_id,
        status=EvaluationRunStatus.COMPLETED,
        aggregates=AggregateMetrics(
            total_cases=1,
            completed_cases=1,
            failed_cases=0,
            pass_rate=1.0,
            mean_latency_ms=105.0,
            metric_averages={"exact_match": 1.0},
            metric_pass_rates={"exact_match": 1.0},
        ),
        completed_at=record.started_at,
    )

    case_res = CaseResult(
        case_id="case_api_1",
        run_id=run_id,
        input="Hello world",
        actual_output="Hello world",
        expected_output="Hello world",
        latency_ms=105.0,
        metrics=[
            MetricResult(
                metric_id="exact_match",
                metric_name="Exact Match",
                score=1.0,
                passed=True,
            )
        ],
    )
    repo.save_case_result(case_res)

    # 1. Default JSON format
    resp_json = client.get(f"/v1/reports/{run_id}?format=json")
    assert resp_json.status_code == 200
    assert resp_json.headers["content-type"].startswith("application/json")
    data = resp_json.json()
    assert data["run_id"] == run_id

    # 2. Markdown format
    resp_md = client.get(f"/v1/reports/{run_id}?format=markdown")
    assert resp_md.status_code == 200
    assert "text/markdown" in resp_md.headers["content-type"]
    assert f"# Evaluation Report: {record.name}" in resp_md.text

    # 3. CSV format
    resp_csv = client.get(f"/v1/reports/{run_id}?format=csv")
    assert resp_csv.status_code == 200
    assert "text/csv" in resp_csv.headers["content-type"]
    assert "case_id,run_id,model_identifier,input" in resp_csv.text
    assert "case_api_1" in resp_csv.text

    # 4. Invalid format
    resp_bad = client.get(f"/v1/reports/{run_id}?format=unsupported_format")
    assert resp_bad.status_code == 400
    assert "Unsupported report format" in resp_bad.json()["detail"]
