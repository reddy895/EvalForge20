"""API endpoints for dashboard analytics, aggregated metrics, and substantiated Git commits."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.evalforge.services.analytics_service import (
    AnalyticsOverviewResponse,
    AnalyticsService,
    CommitAnalyticsResponse,
)
from src.evalforge.storage.database import get_db

analytics_router = APIRouter(prefix="/analytics", tags=["Analytics"])


@analytics_router.get(
    "/overview",
    response_model=AnalyticsOverviewResponse,
    summary="Get aggregated dashboard overview telemetry",
)
async def get_analytics_overview(
    db: AsyncSession = Depends(get_db),
) -> AnalyticsOverviewResponse:
    """Return high-level summary KPIs covering providers, models, evaluation runs, and latency."""
    return await AnalyticsService.get_overview(db)


@analytics_router.get(
    "/commits",
    response_model=CommitAnalyticsResponse,
    summary="Get substantiated Git commit history and milestone tracking",
)
async def get_commit_analytics() -> CommitAnalyticsResponse:
    """Return verified repository commit activity, calendar heatmap data, and target milestone progress."""
    return AnalyticsService.get_commit_analytics()
