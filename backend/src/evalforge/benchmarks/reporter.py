"""Comparison report generator producing grounded summaries and audit metadata."""

from datetime import UTC, datetime

from src.evalforge.experiments.snapshot import DatasetSnapshot
from src.evalforge.schemas.benchmark import (
    BenchmarkComparisonResponse,
    ModelComparisonMetrics,
    ReproducibilityMetadata,
)
from src.evalforge.schemas.evaluation import EvaluationConfig


def generate_comparison_response(
    comparison_id: str,
    name: str,
    snapshot: DatasetSnapshot,
    config: EvaluationConfig,
    matrix: list[ModelComparisonMetrics],
    created_at: datetime | None = None,
) -> BenchmarkComparisonResponse:
    """Construct verified comparison response with complete reproducibility provenance."""
    repro = ReproducibilityMetadata(
        dataset_id=snapshot.dataset_id,
        dataset_version=snapshot.version,
        dataset_snapshot_hash=snapshot.snapshot_hash,
        metrics_evaluated=config.metrics,
        temperature=config.temperature,
        concurrency=config.concurrency,
        executed_at=datetime.now(UTC).isoformat(),
    )

    eval_ids = [m.evaluation_id for m in matrix]
    model_ids = [m.model_id for m in matrix]
    created_iso = (created_at or datetime.now(UTC)).isoformat()

    return BenchmarkComparisonResponse(
        id=comparison_id,
        name=name,
        dataset_id=snapshot.dataset_id,
        dataset_name=snapshot.dataset_name,
        models=model_ids,
        evaluation_ids=eval_ids,
        matrix=matrix,
        reproducibility=repro,
        created_at=created_iso,
    )
