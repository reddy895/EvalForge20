"""Unit tests for deterministic evaluation metrics: Token F1, JSON schema validity, and SLA."""

import pytest

from src.evalforge.evaluation.metrics_json import validate_json_validity
from src.evalforge.evaluation.metrics_sla import evaluate_sla_latency
from src.evalforge.evaluation.metrics_token import compute_token_f1
from src.evalforge.evaluation.scoring import EvaluationScorer


def test_token_f1_exact() -> None:
    res = compute_token_f1("The quick brown fox", "the quick brown fox")
    assert res.f1 == 1.0
    assert res.precision == 1.0
    assert res.recall == 1.0

def test_token_f1_partial() -> None:
    res = compute_token_f1("Paris is the capital of France", "Capital of France is Paris")
    assert res.f1 > 0.8

def test_json_validity() -> None:
    valid, parsed, err = validate_json_validity('```json\n{"status": "ok", "code": 200}\n```')
    assert valid is True
    assert parsed["status"] == "ok"
    assert err is None

    invalid, _, err_msg = validate_json_validity('{bad json')
    assert invalid is False
    assert err_msg is not None

def test_sla_latency() -> None:
    assert evaluate_sla_latency(150.0, 500.0) is True
    assert evaluate_sla_latency(600.0, 500.0) is False

def test_evaluation_scorer_summary() -> None:
    cases = [{"passed": True}, {"passed": False}, {"passed": True}]
    summary = EvaluationScorer.compute_summary_score(cases)
    assert summary["pass_rate"] == 66.7
    assert summary["total_cases"] == 3


@pytest.mark.asyncio
async def test_genuine_zero_score_persistence_and_retrieval_after_simulated_reload() -> None:
    """A genuine zero score (valid inferences that all failed assertions) persists 0.0 and retrieves accurately."""
    import uuid
    from datetime import UTC, datetime
    import pytest
    from src.evalforge.evaluators.aggregator import aggregate_scorecard, is_genuine_zero_score
    from src.evalforge.storage.database import get_session_factory
    from src.evalforge.storage.models.evaluation import CaseResult, EvaluationRun
    from src.evalforge.storage.repositories.evaluation_repo import EvaluationRepository

    session_factory = get_session_factory()
    run_id = f"eval-zero-{uuid.uuid4().hex[:8]}"

    # Two test cases that executed with genuine inference, but completely failed assertion
    c1 = CaseResult(
        evaluation_id=run_id,
        case_id="c1",
        prompt="Write a poem about rust",
        expected_output="Oxidized metal",
        actual_output="I am an AI created by OpenAI",
        passed=False,
        latency_ms=120.0,
        error_message=None,
    )
    c1.metrics = {"exact_match": {"name": "exact_match", "score": 0.0, "passed": False}}

    c2 = CaseResult(
        evaluation_id=run_id,
        case_id="c2",
        prompt="Return valid JSON with key status",
        expected_output="{\"status\": \"ok\"}",
        actual_output="Invalid non-json output",
        passed=False,
        latency_ms=150.0,
        error_message=None,
    )
    c2.metrics = {"exact_match": {"name": "exact_match", "score": 0.0, "passed": False}}

    scorecard = aggregate_scorecard([c1, c2])
    assert is_genuine_zero_score(scorecard) is True
    assert scorecard.pass_rate == 0.0
    assert scorecard.error_count == 0

    # Persist in session 1
    async with session_factory() as session1:
        async with session1.begin():
            repo1 = EvaluationRepository(session1)
            run = EvaluationRun(
                id=run_id,
                name="Genuine Zero Run",
                model_id="zero-candidate-model",
                provider="mock",
                status="completed",
                total_cases=2,
                completed_cases=2,
                passed_cases=0,
                failed_cases=2,
                pass_rate=0.0,
                avg_latency_ms=135.0,
                completed_at=datetime.now(UTC),
            )
            run.summary_metrics = {
                **scorecard.model_dump(),
                "is_genuine_zero": True,
            }
            await repo1.add(run)
            await repo1.add_case_results(run_id, [c1, c2])

    # Simulate fresh page reload / new session
    async with session_factory() as session2:
        repo2 = EvaluationRepository(session2)
        reloaded_run = await repo2.get_with_results(run_id)
        assert reloaded_run is not None
        assert reloaded_run.status == "completed"
        # Crucial: Genuine 0.0 must be preserved as 0.0, NOT null and NOT an error
        assert reloaded_run.pass_rate == 0.0
        assert reloaded_run.avg_latency_ms == 135.0
        assert reloaded_run.passed_cases == 0
        assert reloaded_run.failed_cases == 2
        assert reloaded_run.summary_metrics.get("is_genuine_zero") is True
        assert len(reloaded_run.results) == 2
