"""Modular API route for analytics overview and verified Git commit telemetry."""

from fastapi import APIRouter

from src.evalforge.database.session import get_db_context
from src.evalforge.services.analytics_service import get_analytics_service

router = APIRouter(prefix="/analytics", tags=["analytics"])

@router.get("/overview")
async def get_overview():
    service = get_analytics_service()
    async with get_db_context() as session:
        return await service.get_overview(session)

@router.get("/commits")
def get_commits():
    service = get_analytics_service()
    return service.get_commit_analytics()
