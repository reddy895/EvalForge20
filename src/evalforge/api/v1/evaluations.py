"""API endpoints for Evaluation execution, progress monitoring, and results inspection."""

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.evalforge.schemas.evaluation import (
    CaseResultResponse,
    EvaluationCreateRequest,
    EvaluationDetailResponse,
    EvaluationListResponse,
    EvaluationResponse,
)
from src.evalforge.services.evaluation_service import EvaluationService
from src.evalforge.storage.database import get_db

evaluations_router = APIRouter(prefix="/evaluations", tags=["Evaluations"])


def _map_run_response(run: object) -> EvaluationResponse:
    """Helper formatting EvaluationRun model to EvaluationResponse schema."""
    return EvaluationResponse(
        id=run.id,  # type: ignore[attr-defined]
        name=run.name,  # type: ignore[attr-defined]
        model_id=run.model_id,  # type: ignore[attr-defined]
        provider=run.provider,  # type: ignore[attr-defined]
        dataset_id=run.dataset_id,  # type: ignore[attr-defined]
        dataset_name=run.dataset_name,  # type: ignore[attr-defined]
        status=run.status,  # type: ignore[attr-defined]
        total_cases=run.total_cases,  # type: ignore[attr-defined]
        completed_cases=run.completed_cases,  # type: ignore[attr-defined]
        passed_cases=run.passed_cases,  # type: ignore[attr-defined]
        failed_cases=run.failed_cases,  # type: ignore[attr-defined]
        pass_rate=run.pass_rate,  # type: ignore[attr-defined]
        avg_latency_ms=run.avg_latency_ms,  # type: ignore[attr-defined]
        summary_metrics=run.summary_metrics,  # type: ignore[attr-defined]
        error_message=run.error_message,  # type: ignore[attr-defined]
        created_at=run.created_at.isoformat(),  # type: ignore[attr-defined]
        completed_at=run.completed_at.isoformat() if run.completed_at else None,  # type: ignore[attr-defined]
    )


@evaluations_router.post(
    "",
    response_model=EvaluationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create and start an evaluation run",
)
async def create_evaluation(
    payload: EvaluationCreateRequest,
    db: AsyncSession = Depends(get_db),
) -> EvaluationResponse:
    """Queue and execute an evaluation run over a dataset with bounded concurrency."""
    service = EvaluationService(db)
    run = await service.create_and_start_run(payload)
    return _map_run_response(run)


@evaluations_router.get(
    "",
    response_model=EvaluationListResponse,
    summary="List evaluation runs",
)
async def list_evaluations(
    status_filter: str | None = Query(None, alias="status"),
    model_id: str | None = Query(None),
    dataset_id: str | None = Query(None),
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> EvaluationListResponse:
    """List evaluations filtered by status, target model, or source dataset."""
    service = EvaluationService(db)
    runs = await service.list_evaluations(
        status=status_filter,
        model_id=model_id,
        dataset_id=dataset_id,
        offset=offset,
        limit=limit,
    )
    return EvaluationListResponse(
        total=len(runs),
        items=[_map_run_response(r) for r in runs],
    )


@evaluations_router.get(
    "/{evaluation_id}",
    response_model=EvaluationResponse,
    summary="Get evaluation status and summary",
)
async def get_evaluation(
    evaluation_id: str,
    db: AsyncSession = Depends(get_db),
) -> EvaluationResponse:
    """Fetch current execution status and aggregated metrics scorecard."""
    service = EvaluationService(db)
    run = await service.get_evaluation(evaluation_id)
    return _map_run_response(run)


@evaluations_router.get(
    "/{evaluation_id}/results",
    response_model=EvaluationDetailResponse,
    summary="Get evaluation with individual case results",
)
async def get_evaluation_results(
    evaluation_id: str,
    db: AsyncSession = Depends(get_db),
) -> EvaluationDetailResponse:
    """Retrieve full audit evidence and individual test case outcomes."""
    service = EvaluationService(db)
    run = await service.get_evaluation_with_results(evaluation_id)
    base_resp = _map_run_response(run)

    case_items = [
        CaseResultResponse(
            id=c.id,
            case_id=c.case_id,
            prompt=c.prompt,
            expected_output=c.expected_output,
            actual_output=c.actual_output,
            passed=c.passed,
            latency_ms=c.latency_ms,
            metrics=c.metrics,
            token_usage=c.token_usage,
            error_message=c.error_message,
            created_at=c.created_at.isoformat(),
        )
        for c in run.results
    ]

    return EvaluationDetailResponse(
        **base_resp.model_dump(),
        results=case_items,
    )


@evaluations_router.post(
    "/{evaluation_id}/cancel",
    response_model=EvaluationResponse,
    summary="Cancel an active evaluation run",
)
async def cancel_evaluation(
    evaluation_id: str,
    db: AsyncSession = Depends(get_db),
) -> EvaluationResponse:
    """Signal cooperative cancellation to abort an active evaluation."""
    service = EvaluationService(db)
    run = await service.cancel_evaluation(evaluation_id)
    return _map_run_response(run)
