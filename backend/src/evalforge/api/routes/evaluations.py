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
