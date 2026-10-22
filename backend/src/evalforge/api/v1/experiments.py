"""API endpoints for Experiment definition, parameter tracking, and execution runs."""

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.evalforge.api.v1.evaluations import _map_run_response
from src.evalforge.schemas.evaluation import (
    EvaluationCreateRequest,
    EvaluationListResponse,
    EvaluationResponse,
)
from src.evalforge.services.evaluation_service import EvaluationService
from src.evalforge.storage.database import get_db

experiments_router = APIRouter(prefix="/experiments", tags=["Experiments"])


@experiments_router.post(
    "",
    response_model=EvaluationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create and execute an evaluation experiment",
)
async def create_experiment(
    payload: EvaluationCreateRequest,
    db: AsyncSession = Depends(get_db),
) -> EvaluationResponse:
    """Launch an experimental benchmark run over a parameterized model configuration."""
    service = EvaluationService(db)
    run = await service.create_and_start_run(payload)
    return _map_run_response(run)


@experiments_router.get(
    "",
    response_model=EvaluationListResponse,
    summary="List experimental runs",
)
async def list_experiments(
    status_filter: str | None = Query(None, alias="status"),
    model_id: str | None = Query(None),
    dataset_id: str | None = Query(None),
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> EvaluationListResponse:
    """Retrieve historical experiment runs filtered by model, status, or dataset."""
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


@experiments_router.get(
    "/{experiment_id}",
    response_model=EvaluationResponse,
    summary="Get experiment status and empirical results",
)
async def get_experiment(
    experiment_id: str,
    db: AsyncSession = Depends(get_db),
) -> EvaluationResponse:
    """Inspect parameters, accuracy, latency, and test outcomes for an experiment."""
    service = EvaluationService(db)
    run = await service.get_evaluation(experiment_id)
    return _map_run_response(run)
