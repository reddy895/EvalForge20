"""Unit and API tests for evaluation results export (JSON and CSV)."""

from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from src.evalforge.main import app


class TestEvaluationExport:
    """Verifies that evaluation runs can be exported as structured JSON or CSV."""

    def test_export_not_found_returns_404(self) -> None:
        with TestClient(app) as client:
            resp = client.get("/api/v1/evaluations/non-existent-id/export")
            assert resp.status_code == 404

    def test_export_csv_and_json_format(self) -> None:
        # Mock evaluation service
        fake_run = SimpleNamespace(
            id="run-exp-1",
            name="Test Run Export",
            model_id="qwen2.5:1.5b",
            provider="ollama",
            dataset_id="coding_basics",
            dataset_name="Python Algorithmic Synthesis",
            status="completed",
            total_cases=2,
            completed_cases=2,
            passed_cases=2,
            failed_cases=0,
            pass_rate=1.0,
            avg_latency_ms=120.5,
            summary_metrics={"avg_tokens_per_second": 45.0},
            error_message=None,
            created_at=datetime.now(UTC),
            completed_at=datetime.now(UTC),
            results=[
                SimpleNamespace(
                    id="case-res-1",
                    case_id="case-01",
                    prompt="def rev(s):",
                    expected_output="return s[::-1]",
                    actual_output="return s[::-1]",
                    passed=True,
                    latency_ms=110.0,
                    token_usage={"tokens_per_second": 48.0},
                    metrics={"exact_match": 1.0},
                    error_message=None,
                    created_at=datetime.now(UTC),
                ),
                SimpleNamespace(
                    id="case-res-2",
                    case_id="case-02",
                    prompt="def add(a, b):",
                    expected_output="return a + b",
                    actual_output="return a + b",
                    passed=True,
                    latency_ms=131.0,
                    token_usage={"tokens_per_second": 42.0},
                    metrics={"exact_match": 1.0},
                    error_message=None,
                    created_at=datetime.now(UTC),
                ),
            ],
        )

        with patch("src.evalforge.services.evaluation_service.EvaluationService.get_evaluation_with_results", new=AsyncMock(return_value=fake_run)):
            with TestClient(app) as client:
                # 1. Test CSV export
                csv_resp = client.get("/api/v1/evaluations/run-exp-1/export?format=csv")
                assert csv_resp.status_code == 200
                assert "text/csv" in csv_resp.headers["content-type"]
                assert "eval_run-exp-1.csv" in csv_resp.headers["content-disposition"]
                content = csv_resp.text
                assert "case_id,passed,latency_ms,tokens_per_second" in content
                assert "case-01,True,110.0,48.0" in content
                assert "case-02,True,131.0,42.0" in content

                # 2. Test JSON export
                json_resp = client.get("/api/v1/evaluations/run-exp-1/export?format=json")
                assert json_resp.status_code == 200
                data = json_resp.json()
                assert data["id"] == "run-exp-1"
                assert data["model_id"] == "qwen2.5:1.5b"
                assert len(data["results"]) == 2
                assert data["results"][0]["case_id"] == "case-01"
                assert data["results"][0]["tokens_per_second"] == 48.0
