"""Evaluation application service orchestrating runs, execution, and cancellation."""

import asyncio
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from src.evalforge.core.errors import (
    DataValidationError,
    NotFoundError,
)
from src.evalforge.core.logging import get_logger
from src.evalforge.evaluators.aggregator import aggregate_scorecard
from src.evalforge.experiments.case_runner import CaseRunner
from src.evalforge.experiments.concurrency import BoundedConcurrencyPool
from src.evalforge.experiments.lifecycle import get_lifecycle_coordinator
from src.evalforge.experiments.snapshot import DatasetSnapshot, create_dataset_snapshot
from src.evalforge.providers.registry import get_provider_registry
from src.evalforge.schemas.evaluation import EvaluationConfig, EvaluationCreateRequest
from src.evalforge.storage.database import get_session_factory
from src.evalforge.storage.models.evaluation import CaseResult, EvaluationRun
from src.evalforge.storage.repositories.dataset_repo import DatasetRepository
from src.evalforge.storage.repositories.evaluation_repo import EvaluationRepository

logger = get_logger("evalforge.services.evaluation")


class EvaluationService:
    """Orchestrates evaluation run lifecycle, bounded execution, and result aggregation."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.eval_repo = EvaluationRepository(session)
        self.dataset_repo = DatasetRepository(session)
        self.registry = get_provider_registry()
        self.coordinator = get_lifecycle_coordinator()

    async def create_and_start_run(self, request: EvaluationCreateRequest) -> EvaluationRun:
        """Create a persistent evaluation run and launch execution in the background."""
        # Validate dataset
        dataset = await self.dataset_repo.get_with_cases(request.dataset_id)
        if not dataset:
            raise NotFoundError("Dataset", request.dataset_id)

        if not dataset.test_cases:
            raise DataValidationError(f"Dataset '{dataset.name}' has no test cases to evaluate.")

        # Validate provider
        provider_name = request.provider or "ollama"
        if request.model_id.startswith("mock-"):
            provider_name = "mock"
        self.registry.get(provider_name)

        config = request.config or EvaluationConfig()
        # For local Ollama inference, constrain concurrency to prevent resource thrashing
        if provider_name == "ollama" and config.concurrency > 2:
            config.concurrency = 1

        run_name = request.name or f"{dataset.name} — {request.model_id}"

        # Freeze dataset snapshot for immutable evaluation
        snapshot = create_dataset_snapshot(dataset)
        if request.max_cases and request.max_cases > 0 and request.max_cases < len(snapshot.cases):
            snapshot.cases = snapshot.cases[:request.max_cases]
            snapshot.total_cases = len(snapshot.cases)

        # Create evaluation record
        run = EvaluationRun(
            name=run_name,
            model_id=request.model_id,
            provider=provider_name,
            dataset_id=dataset.id,
            dataset_name=dataset.name,
            status="queued",
            total_cases=len(snapshot.cases),
        )
        run.config = config.model_dump()
        await self.eval_repo.add(run)

        # Launch execution as background task
        asyncio.create_task(
            self._execute_evaluation_task(
                run.id, snapshot, request.model_id, provider_name, config
            )
        )

        return run

    @staticmethod
    async def _execute_evaluation_task(
        evaluation_id: str,
        snapshot: DatasetSnapshot,
        model_id: str,
        provider_name: str,
        config: EvaluationConfig,
    ) -> None:
        """Isolated background runner executing test cases with an independent database session."""
        session_factory = get_session_factory()
        coordinator = get_lifecycle_coordinator()
        cancel_event = coordinator.register_run(evaluation_id)

        async with session_factory() as session:
            repo = EvaluationRepository(session)
            await repo.update_status(evaluation_id, "running")
            await session.commit()

        provider = get_provider_registry().get(provider_name)
        runner = CaseRunner(provider=provider, model_id=model_id, config=config)
        pool = BoundedConcurrencyPool(max_concurrency=config.concurrency)

        try:
            # Execute cases with bounded concurrency
            case_results: list[CaseResult] = await pool.map(
                lambda case: runner.execute_case(case, evaluation_id),
                snapshot.cases,
                cancellation_event=cancel_event,
            )

            # Check if cancelled during run
            if cancel_event.is_set():
                async with session_factory() as session:
                    repo = EvaluationRepository(session)
                    await repo.update_status(evaluation_id, "cancelled")
                    if case_results:
                        await repo.add_case_results(evaluation_id, case_results)
                    await session.commit()
                return

            # Compute aggregate scorecard
            scorecard = aggregate_scorecard(case_results)

            async with session_factory() as session:
                repo = EvaluationRepository(session)
                run = await repo.get(evaluation_id)
                if not run:
                    return
                if scorecard.total_cases > 0 and scorecard.passed_cases == 0 and scorecard.error_count == scorecard.total_cases:
                    run.status = "failed"
                    run.error_message = run.error_message or "All test cases failed due to model inference errors or timeouts."
                elif scorecard.error_count > 0:
                    run.status = "completed_with_errors"
                else:
                    run.status = "completed"
                run.completed_cases = scorecard.completed_cases
                run.passed_cases = scorecard.passed_cases
                run.failed_cases = scorecard.failed_cases
                run.pass_rate = scorecard.pass_rate
                run.avg_latency_ms = scorecard.avg_latency_ms
                run.summary_metrics = scorecard.model_dump()
                run.completed_at = datetime.now(UTC)

                await repo.add_case_results(evaluation_id, case_results)
                await session.commit()

            logger.info(
                "Evaluation '%s' finished with pass rate %.2f", evaluation_id, scorecard.pass_rate
            )

        except Exception as exc:
            logger.exception("Evaluation '%s' execution failed: %s", evaluation_id, exc)
            async with session_factory() as session:
                repo = EvaluationRepository(session)
                await repo.update_status(evaluation_id, "failed", error_message=str(exc))
                await session.commit()

        finally:
            coordinator.unregister_run(evaluation_id)

    async def get_evaluation(self, evaluation_id: str) -> EvaluationRun:
        """Fetch evaluation run metadata."""
        return await self.eval_repo.get_or_fail(evaluation_id, "EvaluationRun")

    async def get_evaluation_with_results(self, evaluation_id: str) -> EvaluationRun:
        """Fetch evaluation run with all case-level results."""
        run = await self.eval_repo.get_with_results(evaluation_id)
        if not run:
            raise NotFoundError("EvaluationRun", evaluation_id)
        return run

    async def list_evaluations(
        self,
        status: str | None = None,
        model_id: str | None = None,
        dataset_id: str | None = None,
        query: str | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[list[EvaluationRun], int]:
        """List evaluations filtered by status, model, dataset, or query, returning matching runs and total count."""
        return await self.eval_repo.list_evaluations(
            status=status,
            model_id=model_id,
            dataset_id=dataset_id,
            query=query,
            offset=offset,
            limit=limit,
        )

    async def cancel_evaluation(self, evaluation_id: str) -> EvaluationRun:
        """Cancel an in-flight evaluation run."""
        run = await self.get_evaluation(evaluation_id)
        if run.status in ("completed", "completed_with_errors", "failed", "cancelled"):
            return run

        self.coordinator.cancel_run(evaluation_id)
        await self.eval_repo.update_status(evaluation_id, "cancelled")
        run.status = "cancelled"
        return run
