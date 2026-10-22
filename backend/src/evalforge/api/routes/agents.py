"""Modular API route for agent evaluations."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from src.evalforge.storage.database import get_db
from src.evalforge.storage.repositories.agent_repo import AgentRepository

router = APIRouter(prefix="/agents", tags=["agents"])

@router.get("")
async def list_agent_evaluations(limit: int = 20, offset: int = 0, db: AsyncSession = Depends(get_db)):
    repo = AgentRepository(db)
    items, total = await repo.list_evaluations(limit=limit, offset=offset)
    return {"total": total, "items": items}
