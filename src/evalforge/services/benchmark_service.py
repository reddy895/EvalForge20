"""Benchmark comparison service coordinating multi-model benchmark runs."""

from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from src.evalforge.benchmarks.comparator import MultiModelComparator
from src.evalforge.benchmarks.reporter import generate_comparison_response
from src.evalforge.benchmarks.statistics import compute_model_metrics
from src.evalforge.core.errors import DataValidationError, NotFoundError
from src.evalforge.core.logging import get_logger
from src.evalforge.experiments.snapshot import create_dataset_snapshot
from src.evalforge.providers.registry import get_provider_registry
from src.evalforge.schemas.benchmark import (
    BenchmarkCompareRequest,
    BenchmarkComparisonResponse,
    ModelComparisonMetrics,
    ReproducibilityMetadata,
)
from src.evalforge.schemas.evaluation import EvaluationConfig
from src.evalforge.storage.models.benchmark import BenchmarkComparison
from src.evalforge.storage.models.evaluation import EvaluationRun
from src.evalforge.storage.repositories.benchmark_repo import BenchmarkRepository
from src.evalforge.storage.repositories.dataset_repo import DatasetRepository
from src.evalforge.storage.repositories.evaluation_repo import EvaluationRepository

logger = get_logger("evalforge.services.benchmark")


class BenchmarkService:
    """Orchestrates multi-model benchmark executions against an identical dataset snapshot."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.benchmark_repo = BenchmarkRepository(session)
        self.dataset_repo = DatasetRepository(session)
        self.eval_repo = EvaluationRepository(session)
        self.registry = get_provider_registry()

    async def compare_models(
        self, request: BenchmarkCompareRequest
    ) -> BenchmarkComparisonResponse:
        """Run multiple models sequentially or concurrently against an immutable dataset snapshot."""
        dataset = await self.dataset_repo.get_with_cases(request.dataset_id)
        if not dataset:
            raise NotFoundError("Dataset", request.dataset_id)
        if not dataset.test_cases:
            raise DataValidationError(f"Dataset '{dataset.name}' has no test cases to evaluate.")

        provider = self.registry.get(request.provider)
        config = request.config or EvaluationConfig()
        snapshot = create_dataset_snapshot(dataset)

        comparator = MultiModelComparator(provider=provider, config=config)

        matrix_items: List[ModelComparisonMetrics] = []
        evaluation_ids: List[str] = []

        comparison_name = request.name or f"Comparison on {dataset.name} ({len(request.models)} models)"

        # Run benchmark for each model against identical snapshot
        for model_id in request.models:
            # Create persistent evaluation record for this model
            run = EvaluationRun(
                name=f"{comparison_name} — {model_id}",
                model_id=model_id,
                provider=request.provider,
                dataset_id=dataset.id,
                dataset_name=dataset.name,
                status="running",
                total_cases=snapshot.total_cases,
            )
            run.config = config.model_dump()
            await self.eval_repo.add(run)
            evaluation_ids.append(run.id)

            # Benchmark model
            case_results = await comparator.benchmark_model(
                model_id=model_id,
                snapshot=snapshot,
                evaluation_id=run.id,
            )

            # Persist results and update run status
            metrics = compute_model_metrics(
                model_id=model_id,
                provider=request.provider,
                evaluation_id=run.id,
                results=case_results,
            )
            matrix_items.append(metrics)

            run.status = "completed"
            run.completed_cases = metrics.total_cases
            run.passed_cases = metrics.passed_cases
            run.failed_cases = metrics.failed_cases
            run.pass_rate = metrics.pass_rate
            run.avg_latency_ms = metrics.avg_latency_ms
            run.completed_at = datetime.now(timezone.utc)

            await self.eval_repo.add_case_results(run.id, case_results)
            await self.session.flush()

        # Persist benchmark comparison
        comparison = BenchmarkComparison(
            name=comparison_name,
            dataset_id=dataset.id,
            dataset_name=dataset.name,
        )
        comparison.model_ids = request.models
        comparison.evaluation_ids = evaluation_ids
        comparison.summary_matrix = [m.model_dump() for m in matrix_items]  # type: ignore[assignment]

        repro = ReproducibilityMetadata(
            dataset_id=snapshot.dataset_id,
            dataset_version=snapshot.version,
            dataset_snapshot_hash=snapshot.snapshot_hash,
            metrics_evaluated=config.metrics,
            temperature=config.temperature,
            concurrency=config.concurrency,
            executed_at=datetime.now(timezone.utc).isoformat(),
        )
        comparison.reproducibility = repro.model_dump()
        await self.benchmark_repo.add(comparison)

        return generate_comparison_response(
            comparison_id=comparison.id,
            name=comparison.name,
            snapshot=snapshot,
            config=config,
            matrix=matrix_items,
            created_at=comparison.created_at,
        )

    async def get_comparison(self, comparison_id: str) -> BenchmarkComparisonResponse:
        """Fetch historical model comparison record by ID."""
        comparison = await self.benchmark_repo.get_or_fail(comparison_id, "BenchmarkComparison")

        matrix_data = [ModelComparisonMetrics(**m) for m in comparison.summary_matrix]  # type: ignore[arg-type]
        repro_data = ReproducibilityMetadata(**comparison.reproducibility)

        return BenchmarkComparisonResponse(
            id=comparison.id,
            name=comparison.name,
            dataset_id=comparison.dataset_id,
            dataset_name=comparison.dataset_name,
            models=comparison.model_ids,
            evaluation_ids=comparison.evaluation_ids,
            matrix=matrix_data,
            reproducibility=repro_data,
            created_at=comparison.created_at.isoformat(),
        )
