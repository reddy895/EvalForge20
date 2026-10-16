"""Application service for running evaluations, persisting results, and retrieving run history."""

from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy.orm import Session

from app.datasets.hasher import compute_cases_hash
from app.datasets.loader import DatasetLoader
from app.domain.models import EvaluationCase
from app.domain.results import AggregateMetrics, CaseResult
from app.domain.state import EvaluationRunStatus
from app.runner.config import EvaluationRunConfig, EvaluationRunRecord
from app.runner.engine import EvaluationRunner
from app.storage.repositories import EvaluationRepository


class EvaluationService:
    """Application coordinator for evaluation execution and persistence."""

    def __init__(self, session: Session):
        self.session = session
        self.repo = EvaluationRepository(session)

    async def run_evaluation(
        self,
        config: EvaluationRunConfig,
        cases_override: list[EvaluationCase] | None = None,
    ) -> tuple[EvaluationRunRecord, list[CaseResult], AggregateMetrics]:
        """Validate input dataset, create persistent run, stream case results, and save aggregates."""
        # 1. Load cases
        cases: list[EvaluationCase] = []
        if cases_override:
            cases = cases_override
        elif config.dataset_cases:
            cases = config.dataset_cases
        elif config.dataset_path:
            report = DatasetLoader.validate_path(Path(config.dataset_path))
            if not report.is_valid:
                raise ValueError(f"Dataset validation failed: {report.format_errors()}")
            cases = report.cases

        else:
            raise ValueError(
                "No dataset cases or dataset path provided in evaluation configuration."
            )

        content_hash = compute_cases_hash(cases)
        # Update config with computed hash
        config = config.model_copy(update={"dataset_version_hash": content_hash})

        # 2. Persist initial run record in PENDING state
        initial_record = EvaluationRunRecord(
            run_id=config.run_id,
            name=config.name,
            config=config,
            total_cases=len(cases),
            started_at=datetime.now(UTC),
        )
        self.repo.create_run(initial_record)

        # 3. Setup callback to persist each completed case immediately (streaming persistence)
        async def on_case_done(res: CaseResult) -> None:
            self.repo.save_case_result(res)

        # 4. Execute runner
        runner = EvaluationRunner(config, on_case_completed=on_case_done)
        record, results, aggregates = await runner.run(cases)

        # 5. Persist final run completion and aggregate metrics
        self.repo.update_run_completion(
            run_id=config.run_id,
            status=record.status,
            aggregates=aggregates,
            completed_at=record.completed_at or datetime.now(UTC),
            error_message=record.error_message,
        )

        record = record.model_copy(update={"metrics": aggregates})
        return record, results, aggregates

    def get_run(self, run_id: str) -> EvaluationRunRecord | None:
        """Retrieve historical run record."""
        return self.repo.get_run(run_id)

    def get_run_results(self, run_id: str) -> list[CaseResult]:
        """Retrieve per-case results for a run."""
        return self.repo.get_case_results(run_id)

    def get_run_aggregates(self, run_id: str) -> AggregateMetrics | None:
        """Retrieve aggregate metrics for a run."""
        return self.repo.get_run_aggregates(run_id)

    def list_runs(
        self,
        limit: int = 50,
        offset: int = 0,
        status: EvaluationRunStatus | str | None = None,
        model_identifier: str | None = None,
        min_pass_rate: float | None = None,
    ) -> list[EvaluationRunRecord]:
        """List historical runs with optional status, model, and pass rate filters."""
        return self.repo.list_runs(
            limit=limit,
            offset=offset,
            status=status,
            model_identifier=model_identifier,
            min_pass_rate=min_pass_rate,
        )
