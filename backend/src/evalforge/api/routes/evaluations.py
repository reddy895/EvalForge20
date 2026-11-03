"""Modular API route for evaluation job execution and history."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.evalforge.storage.database import get_db
from src.evalforge.storage.repositories.evaluation_repo import EvaluationRepository

router = APIRouter(prefix="/evaluations", tags=["evaluations"])

@router.get("")
async def list_evaluations(
    status: str | None = None,
    model_id: str | None = None,
    dataset_id: str | None = None,
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
):
    repo = EvaluationRepository(db)
    runs, total = await repo.list_evaluations(
        status=status,
        model_id=model_id,
        dataset_id=dataset_id,
        limit=limit,
        offset=offset,
    )
    return {"total": total, "items": runs}


@router.get("/{evaluation_id}")
async def get_evaluation_modular(evaluation_id: str):
    """Retrieve evaluation summary with unified fallback across runs and executions."""
    from src.evalforge.api.routes.executions import get_execution_results
    return await get_execution_results(execution_id=evaluation_id)


@router.get("/{evaluation_id}/results")
async def get_evaluation_results_modular(evaluation_id: str):
    """Retrieve full evaluation details and test cases with unified fallback."""
    from src.evalforge.api.routes.executions import get_execution_results
    return await get_execution_results(execution_id=evaluation_id)


@router.get("/{evaluation_id}/export")
async def export_evaluation_modular(
    evaluation_id: str,
    format: str = "json",
    db: AsyncSession = Depends(get_db),
):
    from src.evalforge.api.v1.evaluations import export_evaluation
    return await export_evaluation(evaluation_id=evaluation_id, format=format, db=db)

