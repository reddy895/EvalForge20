"""Modular API route for evaluation job execution and history."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.evalforge.storage.database import get_db
from src.evalforge.storage.repositories.evaluation_repo import EvaluationRepository

router = APIRouter(prefix="/evaluations", tags=["evaluations"])

@router.get("")
async def list_evaluations(limit: int = 50, offset: int = 0, db: AsyncSession = Depends(get_db)):
    repo = EvaluationRepository(db)
    runs, total = await repo.list_evaluations(limit=limit, offset=offset)
    return {"total": total, "items": runs}


@router.get("/{evaluation_id}/export")
async def export_evaluation_modular(
    evaluation_id: str,
    format: str = "json",
    db: AsyncSession = Depends(get_db),
):
    from src.evalforge.api.v1.evaluations import export_evaluation
    return await export_evaluation(evaluation_id=evaluation_id, format=format, db=db)

