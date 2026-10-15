"""Evaluation runner engine orchestrating bounded concurrency and execution lifecycle."""

import asyncio
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime

import app.evaluators  # noqa: F401 - triggers automatic evaluator registration
import app.providers  # noqa: F401 - triggers automatic provider registration
from app.domain.contracts import EvaluatorContract
from app.domain.models import EvaluationCase
from app.domain.results import AggregateMetrics, CaseResult
from app.domain.state import EvaluationRunStatus, validate_status_transition
from app.evaluators.registry import registry
from app.evaluators.summary.aggregator import aggregate_results
from app.providers.base import BaseProvider
from app.providers.registry import provider_registry
from app.runner.config import EvaluationRunConfig, EvaluationRunRecord
from app.runner.executor import execute_case


class EvaluationRunner:
    """Coordinates the end-to-end execution of evaluation test cases with bounded concurrency."""

    def __init__(
        self,
        config: EvaluationRunConfig,
        on_case_completed: Callable[[CaseResult], Awaitable[None]] | None = None,
        on_status_changed: Callable[[EvaluationRunStatus], Awaitable[None]] | None = None,
    ):
        self.config = config
        self.on_case_completed = on_case_completed
        self.on_status_changed = on_status_changed
        self._status = EvaluationRunStatus.PENDING
        self._results: list[CaseResult] = []
        self._is_cancelled = False

    @property
    def status(self) -> EvaluationRunStatus:
        return self._status

    async def _update_status(self, new_status: EvaluationRunStatus) -> None:
        validate_status_transition(self._status, new_status)
        self._status = new_status
        if self.on_status_changed:
            await self.on_status_changed(new_status)

    def cancel(self) -> None:
        """Signal cancellation of ongoing evaluation run."""
        self._is_cancelled = True

    async def run(
        self,
        cases: list[EvaluationCase],
        provider_instance: BaseProvider | None = None,
    ) -> tuple[EvaluationRunRecord, list[CaseResult], AggregateMetrics]:
        """Execute all test cases with bounded concurrency and safe retries."""
        started_at = datetime.now(UTC)
        await self._update_status(EvaluationRunStatus.RUNNING)

        # 1. Resolve Provider
        provider = provider_instance
        if provider is None:
            provider = provider_registry.get(
                self.config.target.provider_name,
                model_identifier=self.config.target.model_identifier,
                base_url=self.config.target.base_url,
                timeout_seconds=self.config.timeout_seconds,
            )

        # 2. Resolve Evaluators
        evaluators_map: dict[str, EvaluatorContract] = {}
        for eval_cfg in self.config.evaluators:
            if eval_cfg.metric_id not in evaluators_map:
                evaluators_map[eval_cfg.metric_id] = registry.get(eval_cfg.metric_id)

        # 3. Setup Bounded Concurrency
        semaphore = asyncio.Semaphore(self.config.max_concurrency)
        results: list[CaseResult] = []
        categories_map: dict[str, str | None] = {c.id: c.category for c in cases}

        async def worker(case: EvaluationCase) -> CaseResult:
            if self._is_cancelled:
                return CaseResult(
                    case_id=case.id,
                    run_id=self.config.run_id,
                    input=case.input,
                    expected_output=case.expected_output,
                    error_category="cancelled",
                    error_message="Evaluation run was cancelled",
                )

            async with semaphore:
                if self._is_cancelled:
                    return CaseResult(
                        case_id=case.id,
                        run_id=self.config.run_id,
                        input=case.input,
                        expected_output=case.expected_output,
                        error_category="cancelled",
                        error_message="Evaluation run was cancelled",
                    )

                res = await execute_case(
                    case=case,
                    provider=provider,
                    target_config=self.config.target,
                    evaluator_configs=self.config.evaluators,
                    evaluators_map=evaluators_map,
                    run_id=self.config.run_id,
                    max_retries=self.config.max_retries,
                )

                if self.on_case_completed:
                    await self.on_case_completed(res)

                return res

        # Run cases concurrently up to semaphore limit
        tasks = [asyncio.create_task(worker(c)) for c in cases]
        try:
            completed_results = await asyncio.gather(*tasks, return_exceptions=True)
            for item in completed_results:
                if isinstance(item, CaseResult):
                    results.append(item)
                elif isinstance(item, Exception):
                    # Unhandled error in case worker
                    results.append(
                        CaseResult(
                            case_id="error",
                            run_id=self.config.run_id,
                            input="unknown",
                            error_category="execution_error",
                            error_message=str(item),
                        )
                    )
        except Exception as exc:
            # Preserve whatever was already completed
            for t in tasks:
                if t.done() and not t.cancelled():
                    res = t.result()
                    if isinstance(res, CaseResult) and res not in results:
                        results.append(res)
            self._results = results
            await self._update_status(EvaluationRunStatus.FAILED)
            raise exc

        self._results = results

        # 4. Compute Aggregate Metrics
        aggregates = aggregate_results(results, case_categories=categories_map)

        # 5. Determine Final Run Status
        completed_at = datetime.now(UTC)
        if self._is_cancelled:
            final_status = EvaluationRunStatus.CANCELLED
        elif aggregates.failed_cases > 0 and aggregates.completed_cases > 0:
            final_status = EvaluationRunStatus.COMPLETED_WITH_ERRORS
        elif aggregates.failed_cases == len(cases) and len(cases) > 0:
            final_status = EvaluationRunStatus.FAILED
        else:
            final_status = EvaluationRunStatus.COMPLETED

        await self._update_status(final_status)

        record = EvaluationRunRecord(
            run_id=self.config.run_id,
            name=self.config.name,
            status=final_status,
            config=self.config,
            total_cases=len(cases),
            completed_cases=aggregates.completed_cases,
            failed_cases=aggregates.failed_cases,
            started_at=started_at,
            completed_at=completed_at,
        )

        return record, results, aggregates
