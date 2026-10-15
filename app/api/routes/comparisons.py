"""Run comparison and regression detection API routes."""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.application.evaluation_service import EvaluationService
from app.comparisons.comparator import (
    ComparisonResult,
    RegressionThresholds,
    compare_evaluation_runs,
)
from app.comparisons.multi_comparator import (
    MultiRunComparisonMatrix,
    compare_multiple_runs,
)
from app.storage.database import get_db

comparisons_router = APIRouter(prefix="/v1", tags=["Comparisons"])


class CompareRunsRequest(BaseModel):
    """Payload to compare two evaluation runs and evaluate regression thresholds."""

    baseline_run_id: str = Field(..., description="Run ID of the baseline benchmark")
    candidate_run_id: str = Field(..., description="Run ID of the new candidate to evaluate")
    thresholds: RegressionThresholds = Field(default_factory=RegressionThresholds)
    allow_different_datasets: bool = Field(default=False)


@comparisons_router.post(
    "/compare",
    response_model=ComparisonResult,
    summary="Compare two evaluation runs and check for regressions",
)
async def compare_runs_endpoint(
    req: CompareRunsRequest,
    db: Session = Depends(get_db),
) -> ComparisonResult:
    """Compare candidate against baseline, reporting deltas and threshold violations."""
    service = EvaluationService(db)

    baseline = service.get_run(req.baseline_run_id)
    if not baseline:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Baseline run '{req.baseline_run_id}' not found",
        )

    candidate = service.get_run(req.candidate_run_id)
    if not candidate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Candidate run '{req.candidate_run_id}' not found",
        )

    base_cases = service.get_run_results(req.baseline_run_id)
    base_aggs = service.get_run_aggregates(req.baseline_run_id)
    cand_cases = service.get_run_results(req.candidate_run_id)
    cand_aggs = service.get_run_aggregates(req.candidate_run_id)

    if not base_aggs or not cand_aggs:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Both baseline and candidate runs must have completed aggregate metrics before comparing",
        )

    try:
        return compare_evaluation_runs(
            baseline=baseline,
            baseline_cases=base_cases,
            baseline_aggs=base_aggs,
            candidate=candidate,
            candidate_cases=cand_cases,
            candidate_aggs=cand_aggs,
            thresholds=req.thresholds,
            allow_different_datasets=req.allow_different_datasets,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


class CompareMatrixRequest(BaseModel):
    """Payload to compare multiple evaluation runs across models."""

    run_ids: list[str] = Field(
        ..., min_length=2, description="List of run IDs to benchmark together"
    )


@comparisons_router.post(
    "/compare/matrix",
    response_model=MultiRunComparisonMatrix,
    summary="Compare two or more evaluation runs across models, metrics, and case disagreements",
)
async def compare_matrix_endpoint(
    req: CompareMatrixRequest,
    db: Session = Depends(get_db),
) -> MultiRunComparisonMatrix:
    """Generate multi-run comparison matrix across models, latencies, and accuracy."""
    service = EvaluationService(db)
    runs = []
    cases_by_run = {}

    for r_id in req.run_ids:
        r = service.get_run(r_id)
        if not r:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Evaluation run '{r_id}' not found",
            )
        runs.append(r)
        cases_by_run[r_id] = service.get_run_results(r_id)

    try:
        return compare_multiple_runs(runs=runs, cases_by_run=cases_by_run)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

