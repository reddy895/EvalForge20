"""Modular API route for benchmark matrices."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from src.evalforge.storage.database import get_db
from src.evalforge.storage.repositories.benchmark_repo import BenchmarkRepository

router = APIRouter(prefix="/benchmarks", tags=["benchmarks"])

@router.get("")
async def list_benchmarks(limit: int = 20, offset: int = 0, db: AsyncSession = Depends(get_db)):
    repo = BenchmarkRepository(db)
    items, total = await repo.list_comparisons(limit=limit, offset=offset)
    return {"total": total, "items": items}
