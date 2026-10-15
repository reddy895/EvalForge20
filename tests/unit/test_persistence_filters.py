"""Unit tests for evaluation run filtering by status, model, and metric thresholds."""

from datetime import UTC, datetime

from app.application.evaluation_service import EvaluationService
from app.domain.models import TargetConfiguration, TargetType
from app.domain.results import AggregateMetrics
from app.domain.state import EvaluationRunStatus
from app.runner.config import EvaluationRunConfig, EvaluationRunRecord
from app.storage.models import Base
from app.storage.repositories import EvaluationRepository
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker


def test_repository_run_filtering():
    """Verify list_runs correctly filters by status, model_identifier, and min_pass_rate."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine)
    session: Session = session_factory()

    repo = EvaluationRepository(session)
    service = EvaluationService(session)

    # Create 3 runs with different models and statuses
    run1 = EvaluationRunRecord(
        run_id="run_qwen_1",
        name="Qwen Run",
        status=EvaluationRunStatus.COMPLETED,
        config=EvaluationRunConfig(
            run_id="run_qwen_1",
            target=TargetConfiguration(
                target_name="Qwen Target",
                target_type=TargetType.OLLAMA,
                provider_name="ollama",
                model_identifier="qwen2.5:3b",
            ),
        ),
        total_cases=10,
        completed_cases=10,
        failed_cases=0,
        started_at=datetime.now(UTC),
    )
    repo.create_run(run1)
    repo.update_run_completion(
        run_id="run_qwen_1",
        status=EvaluationRunStatus.COMPLETED,
        aggregates=AggregateMetrics(
            total_cases=10,
            completed_cases=10,
            failed_cases=0,
            pass_rate=0.9,
            mean_latency_ms=150.0,
        ),
        completed_at=datetime.now(UTC),
    )

    run2 = EvaluationRunRecord(
        run_id="run_llama_1",
        name="Llama Run",
        status=EvaluationRunStatus.COMPLETED,
        config=EvaluationRunConfig(
            run_id="run_llama_1",
            target=TargetConfiguration(
                target_name="Llama Target",
                target_type=TargetType.OLLAMA,
                provider_name="ollama",
                model_identifier="llama3.2:1b",
            ),
        ),
        total_cases=10,
        completed_cases=10,
        failed_cases=0,
        started_at=datetime.now(UTC),
    )
    repo.create_run(run2)
    repo.update_run_completion(
        run_id="run_llama_1",
        status=EvaluationRunStatus.COMPLETED,
        aggregates=AggregateMetrics(
            total_cases=10,
            completed_cases=10,
            failed_cases=0,
            pass_rate=0.4,
            mean_latency_ms=80.0,
        ),
        completed_at=datetime.now(UTC),
    )

    run3 = EvaluationRunRecord(
        run_id="run_failed_1",
        name="Failed Run",
        status=EvaluationRunStatus.FAILED,
        config=EvaluationRunConfig(
            run_id="run_failed_1",
            target=TargetConfiguration(
                target_name="Failed Target",
                target_type=TargetType.OLLAMA,
                provider_name="ollama",
                model_identifier="qwen2.5:3b",
            ),
        ),
        total_cases=10,
        completed_cases=0,
        failed_cases=10,
        started_at=datetime.now(UTC),
    )
    repo.create_run(run3)

    # 1. Total runs without filters
    all_runs = service.list_runs()
    assert len(all_runs) == 3

    # 2. Filter by status COMPLETED
    completed_runs = service.list_runs(status=EvaluationRunStatus.COMPLETED)
    assert len(completed_runs) == 2
    assert all(r.status == EvaluationRunStatus.COMPLETED for r in completed_runs)

    # 3. Filter by model_identifier
    qwen_runs = service.list_runs(model_identifier="qwen2.5:3b")
    assert len(qwen_runs) == 2
    assert {r.run_id for r in qwen_runs} == {"run_qwen_1", "run_failed_1"}

    # 4. Filter by min_pass_rate >= 0.8
    high_perf = service.list_runs(min_pass_rate=0.8)
    assert len(high_perf) == 1
    assert high_perf[0].run_id == "run_qwen_1"

    # 5. Combined filter: model="qwen2.5:3b" and status=COMPLETED
    qwen_completed = service.list_runs(
        model_identifier="qwen2.5:3b",
        status=EvaluationRunStatus.COMPLETED,
    )
    assert len(qwen_completed) == 1
    assert qwen_completed[0].run_id == "run_qwen_1"

    session.close()
