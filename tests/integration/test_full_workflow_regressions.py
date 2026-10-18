"""End-to-end integration tests for run comparisons, regression gates, and multi-evaluator execution."""

from pathlib import Path

import pytest
from app.application.evaluation_service import EvaluationService
from app.cli.main import cli_app
from app.comparisons.comparator import (
    RegressionThresholds,
    compare_evaluation_runs,
)
from app.domain.models import EvaluatorConfiguration, TargetConfiguration
from app.runner.config import EvaluationRunConfig
from app.storage.database import get_session_factory, init_db
from typer.testing import CliRunner


@pytest.mark.asyncio
async def test_end_to_end_regression_gate_failure(tmp_path: Path):
    """Verify that a candidate run with degraded accuracy triggers a regression failure."""
    init_db()
    session_factory = get_session_factory()

    # 1. Baseline run (perfect score with echo)
    with session_factory() as session:
        service = EvaluationService(session)
        base_cfg = EvaluationRunConfig(
            name="Baseline Run",
            target=TargetConfiguration(
                target_name="mock_base",
                provider_name="mock",
                model_identifier="echo",
                extra_params={
                    "canned_responses": {
                        "France": "Paris",
                        "15 multiplied": "60",
                        "bloops": "Yes",
                        "Return a JSON": '{"status":"ok"}',
                    }
                },
            ),
            evaluators=[
                EvaluatorConfiguration(evaluator_name="exact_match", metric_id="exact_match")
            ],
            dataset_path="examples/datasets/basic.jsonl",
        )
        base_rec, _, base_aggs = await service.run_evaluation(base_cfg)

    # 2. Candidate run (degraded score with static provider that mismatches)
    with session_factory() as session:
        service = EvaluationService(session)
        cand_cfg = EvaluationRunConfig(
            name="Candidate Run",
            target=TargetConfiguration(
                target_name="mock_cand",
                provider_name="mock",
                model_identifier="wrong",
                extra_params={"default_response": "wrong answer"},
            ),
            evaluators=[
                EvaluatorConfiguration(evaluator_name="exact_match", metric_id="exact_match")
            ],
            dataset_path="examples/datasets/basic.jsonl",
        )
        cand_rec, _, cand_aggs = await service.run_evaluation(cand_cfg)

    # 3. Compare runs with strict regression thresholds
    with session_factory() as session:
        service = EvaluationService(session)
        base_cases = service.get_run_results(base_rec.run_id)
        cand_cases = service.get_run_results(cand_rec.run_id)

    comparison = compare_evaluation_runs(
        baseline=base_rec,
        candidate=cand_rec,
        baseline_cases=base_cases,
        candidate_cases=cand_cases,
        baseline_aggs=base_aggs,
        candidate_aggs=cand_aggs,
        thresholds=RegressionThresholds(
            max_allowed_pass_rate_drop=0.05, max_allowed_regressed_cases=0
        ),
    )

    # Candidate pass rate dropped from 1.0 to 0.0 -> Quality gate must FAIL
    assert comparison.passed_regression_gate is False
    assert len(comparison.threshold_violations) > 0
    assert any("Pass rate dropped" in v for v in comparison.threshold_violations)
    assert len(comparison.regressed_cases) > 0


def test_cli_compare_command_integration():
    """Verify CLI compare command exits with code 1 on regression and code 0 on parity."""
    runner = CliRunner()
    init_db()

    # Launch two runs via CLI evaluate command
    res1 = runner.invoke(
        cli_app,
        [
            "evaluate",
            "--dataset",
            "examples/datasets/basic.jsonl",
            "--provider",
            "mock",
            "--model",
            "echo",
        ],
    )
    assert res1.exit_code == 0
    run_id_1 = [
        line.split(":")[-1].strip()
        for line in res1.stdout.splitlines()
        if "Starting evaluation run" in line
    ][0]

    res2 = runner.invoke(
        cli_app,
        [
            "evaluate",
            "--dataset",
            "examples/datasets/basic.jsonl",
            "--provider",
            "mock",
            "--model",
            "echo",
        ],
    )
    assert res2.exit_code == 0
    run_id_2 = [
        line.split(":")[-1].strip()
        for line in res2.stdout.splitlines()
        if "Starting evaluation run" in line
    ][0]

    # Compare identical runs -> should pass quality gate with exit code 0
    cmp_res = runner.invoke(
        cli_app,
        ["compare", run_id_1, run_id_2, "--max-drop", "0.05"],
    )
    assert cmp_res.exit_code == 0
    assert "Quality Gate: [PASSED]" in cmp_res.stdout


@pytest.mark.asyncio
async def test_full_lifecycle_evaluation_task_analysis_and_export(tmp_path: Path):
    """Verify full end-to-end evaluation lifecycle: multi-evaluator execution, task analysis, and multi-format exports."""
    from app.api.routes.task_analysis import get_run_task_analysis
    from app.reporting.csv_exporter import generate_csv_report
    from app.reporting.json_exporter import generate_json_report
    from app.reporting.markdown_exporter import generate_markdown_report

    init_db()
    session_factory = get_session_factory()

    with session_factory() as session:
        service = EvaluationService(session)
        cfg = EvaluationRunConfig(
            name="Full Lifecycle Verification Run",
            target=TargetConfiguration(
                target_name="mock_lifecycle",
                provider_name="mock",
                model_identifier="echo",
                extra_params={
                    "canned_responses": {
                        "France": "Paris",
                        "15 multiplied": "60",
                        "bloops": "Yes",
                        "Return a JSON": '{"status":"ok"}',
                    }
                },
            ),
            evaluators=[
                EvaluatorConfiguration(evaluator_name="exact_match", metric_id="exact_match"),
                EvaluatorConfiguration(evaluator_name="contains_match", metric_id="contains_match"),
            ],
            dataset_path="examples/datasets/basic.jsonl",
        )
        record, results, aggregates = await service.run_evaluation(cfg)

        assert record.status.value == "completed"
        assert record.completed_cases == 4
        assert aggregates.pass_rate is not None
        assert len(results) == 4

        # Task analysis route check
        analysis = await get_run_task_analysis(record.run_id, db=session)
        assert analysis.run_id == record.run_id
        assert analysis.total_cases == 4
        assert isinstance(analysis.complexity_bands, dict)
        assert len(analysis.task_categories) > 0

        # Export generators check
        json_rep = generate_json_report(record, results, aggregates, redact_inputs=True)
        assert json_rep["run_id"] == record.run_id
        assert json_rep["per_case_results"][0]["input"] == "[REDACTED_PROMPT]"

        md_rep = generate_markdown_report(record, results, aggregates, redact_inputs=True)
        assert f"# Evaluation Report: {record.name}" in md_rep
        assert "[REDACTED_PROMPT]" in md_rep

        csv_rep = generate_csv_report(record, results, redact_inputs=True)
        assert "case_id,run_id,model_identifier" in csv_rep
        assert "[REDACTED_PROMPT]" in csv_rep
