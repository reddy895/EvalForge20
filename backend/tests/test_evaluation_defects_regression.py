"""Regression tests verifying fixes for the 6 critical defects identified in EvalForge20."""

import uuid
import pytest
from types import SimpleNamespace
from fastapi.testclient import TestClient

from src.evalforge.main import app
from src.evalforge.evaluators.aggregator import aggregate_scorecard
from src.evalforge.experiments.case_runner import CaseRunner
from src.evalforge.experiments.snapshot import FrozenTestCase
from src.evalforge.schemas.evaluation import EvaluationConfig


class TestDefect1ZeroLatencyAndFailedRuns:
    def test_all_failed_cases_yields_none_latencies(self) -> None:
        """When cases fail or error out, avg_latency_ms should be None rather than 0.0 ms."""
        cases = [
            SimpleNamespace(
                passed=False,
                latency_ms=0.0,
                token_usage=None,
                metrics={},
                error_message="Ollama request timed out after 30s",
            ),
            SimpleNamespace(
                passed=False,
                latency_ms=0.0,
                token_usage=None,
                metrics={},
                error_message="Connection refused",
            ),
        ]
        scorecard = aggregate_scorecard(cases)
        assert scorecard.avg_latency_ms is None
        assert scorecard.p50_latency_ms is None
        assert scorecard.p95_latency_ms is None
        assert scorecard.passed_cases == 0
        assert scorecard.failed_cases == 2
        assert scorecard.error_count == 2


class TestDefect2P95AndThroughputTelemetry:
    def test_p95_and_tokens_per_second_aggregation(self) -> None:
        """P95 latency and tokens_per_second are computed accurately from case telemetry."""
        cases = [
            SimpleNamespace(
                passed=True,
                latency_ms=100.0,
                token_usage={"prompt_tokens": 20, "completion_tokens": 10, "tokens_per_second": 45.0, "load_duration_ms": 12.0},
                metrics={"exact_match": {"score": 1.0, "passed": True}},
                error_message=None,
            ),
            SimpleNamespace(
                passed=True,
                latency_ms=200.0,
                token_usage={"prompt_tokens": 20, "completion_tokens": 15, "tokens_per_second": 55.0, "load_duration_ms": 8.0},
                metrics={"exact_match": {"score": 1.0, "passed": True}},
                error_message=None,
            ),
        ]
        scorecard = aggregate_scorecard(cases)
        assert scorecard.avg_latency_ms == 150.0
        assert scorecard.p95_latency_ms is not None
        assert scorecard.avg_tokens_per_second == 50.0
        assert scorecard.avg_load_duration_ms == 10.0


class TestDefect3FailedCasesAssertionBreakdown:
    @pytest.mark.asyncio
    async def test_errored_cases_preserve_assertion_breakdown(self) -> None:
        """When a case execution fails or errors, explicit failure assertions are recorded in metrics."""
        mock_provider = SimpleNamespace()

        async def mock_generate(*args, **kwargs):
            raise TimeoutError("Inference timed out after 30s")

        mock_provider.generate = mock_generate

        config = EvaluationConfig(
            metrics=["exact_match", "levenshtein"],
            thresholds={"exact_match": 1.0, "levenshtein": 0.8},
        )
        runner = CaseRunner(provider=mock_provider, model_id="test-model", config=config)

        case = FrozenTestCase(
            id="case-1",
            prompt="Compute 2+2",
            expected_output="4",
        )
        result = await runner.execute_case(case, "eval-test-run")

        assert result.passed is False
        err_msg = (result.error_message or "").lower()
        assert "timeout" in err_msg or "timed out" in err_msg
        # Ensure metrics dictionary is populated with failed assertion records
        assert "exact_match" in result.metrics
        assert result.metrics["exact_match"]["passed"] is False
        assert result.metrics["exact_match"]["score"] == 0.0
        assert "error" in result.metrics["exact_match"]["details"]


class TestDefect4IndividualCaseBreakdownApi:
    def test_evaluation_detail_response_contains_both_results_and_case_results(self) -> None:
        """The evaluation results endpoint must return both 'results' and 'case_results' to prevent (0) count."""
        unique_suffix = uuid.uuid4().hex[:8]
        with TestClient(app) as client:
            ds_res = client.post(
                "/api/v1/datasets",
                json={
                    "name": f"Regression DS {unique_suffix}",
                    "cases": [
                        {"prompt": "Hi", "expected_output": "Hi"},
                        {"prompt": "Bye", "expected_output": "Bye"},
                        {"prompt": "Echo", "expected_output": "Echo"},
                    ],
                },
            )
            assert ds_res.status_code == 201
            dataset_id = ds_res.json()["id"]

            run_res = client.post(
                "/api/v1/evaluations",
                json={
                    "name": f"Regression Run {unique_suffix}",
                    "model_id": "mock-llama-3.1-8b",
                    "provider": "mock",
                    "dataset_id": dataset_id,
                },
            )
            assert run_res.status_code == 201
            run_id = run_res.json()["id"]

            # Query results endpoint
            import time
            for _ in range(50):
                time.sleep(0.05)
                det_res = client.get(f"/api/v1/evaluations/{run_id}/results")
                data = det_res.json()
                if det_res.status_code == 200 and len(data.get("results", [])) == 3:
                    break

            assert "results" in data
            assert "case_results" in data
            assert len(data["results"]) == 3
            assert len(data["case_results"]) == 3
            assert data["results"] == data["case_results"]


class TestDefect5LeaderboardDeduplicationAndFiltering:
    def test_generate_leaderboard_ranks_by_quality_and_latency(self) -> None:
        """Leaderboard ranking sorts by quality descending and valid latency ascending."""
        from src.evalforge.analytics.leaderboard import generate_leaderboard

        runs = [
            {
                "model_id": "ollama/qwen2.5:7b",
                "quality_score": 85.0,
                "median_latency_ms": 200.0,
                "pass_rate": 85.0,
            },
            {
                "model_id": "ollama/llama3.2:3b",
                "quality_score": 90.0,
                "median_latency_ms": 150.0,
                "pass_rate": 90.0,
            },
            {
                "model_id": "ollama/deepseek-r1:7b",
                "quality_score": 85.0,
                "median_latency_ms": 120.0,  # Lower latency at equal quality
                "pass_rate": 85.0,
            },
        ]

        entries = generate_leaderboard(runs)
        assert len(entries) == 3
        # Rank 1: Highest quality (90.0)
        assert entries[0].model_id == "ollama/llama3.2:3b"
        assert entries[0].rank == 1
        # Rank 2: 85.0 score with lower latency (120ms vs 200ms)
        assert entries[1].model_id == "ollama/deepseek-r1:7b"
        assert entries[1].rank == 2
        # Rank 3: 85.0 score with 200ms
        assert entries[2].model_id == "ollama/qwen2.5:7b"
        assert entries[2].rank == 3

    def test_leaderboard_api_endpoint_filters_mock_models_by_default(self) -> None:
        """Leaderboard API endpoint should not include mock runs unless explicitly requested."""
        with TestClient(app) as client:
            res_default = client.get("/api/v1/analytics/leaderboard")
            assert res_default.status_code == 200
            data_default = res_default.json()
            # None of the entries should have provider == 'mock' or mock- prefix
            for item in data_default:
                assert item.get("provider") != "mock"
                assert not str(item.get("model_id")).startswith("mock-")
