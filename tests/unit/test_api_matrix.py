"""Unit tests for multi-run comparison matrix REST API endpoint."""

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


def test_compare_matrix_api(client: TestClient):
    """Verify /v1/compare/matrix computes correct matrix rankings across multiple runs."""
    db = next(get_db())
    repo = EvaluationRepository(db)

    # Run 1: Qwen
    r1 = EvaluationRunRecord(
        run_id="matrix_run_qwen",
        name="Qwen Matrix Run",
        status=EvaluationRunStatus.COMPLETED,
        config=EvaluationRunConfig(
            run_id="matrix_run_qwen",
            target=TargetConfiguration(
                target_name="Qwen Target",
                target_type=TargetType.OLLAMA,
                provider_name="ollama",
                model_identifier="qwen2.5:3b",
            ),
        ),
        total_cases=2,
        completed_cases=2,
        failed_cases=0,
    )
    repo.create_run(r1)
    repo.update_run_completion(
        run_id="matrix_run_qwen",
        status=EvaluationRunStatus.COMPLETED,
        aggregates=AggregateMetrics(
            total_cases=2,
            completed_cases=2,
            failed_cases=0,
            pass_rate=1.0,
            mean_latency_ms=120.0,
            metric_averages={"exact_match": 1.0},
        ),
        completed_at=r1.started_at,
    )

    # Run 2: Llama
    r2 = EvaluationRunRecord(
        run_id="matrix_run_llama",
        name="Llama Matrix Run",
        status=EvaluationRunStatus.COMPLETED,
        config=EvaluationRunConfig(
            run_id="matrix_run_llama",
            target=TargetConfiguration(
                target_name="Llama Target",
                target_type=TargetType.OLLAMA,
                provider_name="ollama",
                model_identifier="llama3.2:1b",
            ),
        ),
        total_cases=2,
        completed_cases=2,
        failed_cases=0,
    )
    repo.create_run(r2)
    repo.update_run_completion(
        run_id="matrix_run_llama",
        status=EvaluationRunStatus.COMPLETED,
        aggregates=AggregateMetrics(
            total_cases=2,
            completed_cases=2,
            failed_cases=0,
            pass_rate=0.5,
            mean_latency_ms=65.0,
            metric_averages={"exact_match": 0.5},
        ),
        completed_at=r2.started_at,
    )

    # Case results
    repo.save_case_result(
        CaseResult(
            case_id="m_case_1",
            run_id="matrix_run_qwen",
            input="Test 1",
            actual_output="Pass",
            metrics=[
                MetricResult(metric_id="exact_match", metric_name="EM", score=1.0, passed=True)
            ],
        )
    )
    repo.save_case_result(
        CaseResult(
            case_id="m_case_1",
            run_id="matrix_run_llama",
            input="Test 1",
            actual_output="Fail",
            metrics=[
                MetricResult(metric_id="exact_match", metric_name="EM", score=0.0, passed=False)
            ],
        )
    )

    # Send API request
    payload = {"run_ids": ["matrix_run_qwen", "matrix_run_llama"]}
    resp = client.post("/v1/compare/matrix", json=payload)
    assert resp.status_code == 200

    data = resp.json()
    assert len(data["runs"]) == 2
    assert data["fastest_run_id"] == "matrix_run_llama"
    assert data["highest_accuracy_run_id"] == "matrix_run_qwen"
    assert len(data["case_disagreements"]) == 1
    assert data["case_disagreements"][0]["case_id"] == "m_case_1"
    assert "Compared 2 evaluation runs" in data["summary"]
