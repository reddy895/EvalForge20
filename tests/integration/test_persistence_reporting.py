"""Integration tests verifying persistence across application restarts and report correctness."""

import json
from pathlib import Path

import pytest
from app.application.evaluation_service import EvaluationService
from app.domain.models import EvaluatorConfiguration, TargetConfiguration, TargetType
from app.domain.state import EvaluationRunStatus
from app.reporting.json_exporter import export_report_to_file, generate_json_report
from app.runner.config import EvaluationRunConfig
from app.storage.database import get_engine, get_session_factory, init_db


@pytest.mark.asyncio
async def test_persistence_across_restarts(tmp_path: Path):
    """Verify evaluation runs, cases, and metrics persist and can be reloaded after full restart."""
    db_file = tmp_path / "persistent_test.db"
    db_url = f"sqlite:///{db_file}"

    # --- Phase 1: Initialize DB and execute an evaluation run ---
    engine1 = get_engine(db_url)
    init_db(engine1)
    session_factory1 = get_session_factory(engine1)

    target_cfg = TargetConfiguration(
        target_name="mock-target",
        target_type=TargetType.MOCK,
        provider_name="mock",
        model_identifier="mock-model-v1",
    )
    evaluators = [
        EvaluatorConfiguration(evaluator_name="Exact Match", metric_id="exact_match"),
    ]

    with session_factory1() as session1:
        service1 = EvaluationService(session1)
        config = EvaluationRunConfig(
            name="Restart Persistence Test",
            dataset_path="examples/datasets/basic.jsonl",
            target=target_cfg,
            evaluators=evaluators,
        )
        record1, results1, aggregates1 = await service1.run_evaluation(config)
        run_id = record1.run_id
        assert record1.status == EvaluationRunStatus.COMPLETED
        assert len(results1) == 4

    # Close and dispose engine 1 (simulate application shutdown)
    engine1.dispose()

    # --- Phase 2: Reopen from scratch using new engine and session ---
    engine2 = get_engine(db_url)
    session_factory2 = get_session_factory(engine2)

    with session_factory2() as session2:
        service2 = EvaluationService(session2)

        # Retrieve run record
        reloaded_run = service2.get_run(run_id)
        assert reloaded_run is not None
        assert reloaded_run.run_id == run_id
        assert reloaded_run.name == "Restart Persistence Test"
        assert reloaded_run.status == EvaluationRunStatus.COMPLETED
        assert reloaded_run.total_cases == 4
        assert reloaded_run.completed_cases == 4

        # Retrieve case results
        reloaded_cases = service2.get_run_results(run_id)
        assert len(reloaded_cases) == 4
        for case in reloaded_cases:
            assert case.run_id == run_id
            assert case.actual_output is not None
            assert len(case.metrics) >= 1

        # Retrieve aggregates
        reloaded_aggs = service2.get_run_aggregates(run_id)
        assert reloaded_aggs is not None
        assert reloaded_aggs.total_cases == 4

        # Generate and export JSON report
        report_data = generate_json_report(reloaded_run, reloaded_cases, reloaded_aggs)
        assert report_data["report_schema_version"] == "1.0.0"
        assert report_data["run_id"] == run_id
        assert len(report_data["per_case_results"]) == 4

        export_path = tmp_path / "report_out.json"
        export_report_to_file(export_path, report_data)
        assert export_path.exists()

        loaded_json = json.loads(export_path.read_text(encoding="utf-8"))
        assert loaded_json["run_id"] == run_id
        assert loaded_json["status"] == "completed"

    engine2.dispose()
