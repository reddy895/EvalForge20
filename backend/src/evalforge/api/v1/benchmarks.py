"""API endpoints for multi-model benchmark comparisons and matrix reports."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.evalforge.schemas.benchmark import (
    BenchmarkCompareRequest,
    BenchmarkComparisonResponse,
)
from src.evalforge.services.benchmark_service import BenchmarkService
from src.evalforge.storage.database import get_db

benchmarks_router = APIRouter(prefix="/benchmarks", tags=["Benchmarks"])


@benchmarks_router.post(
    "/compare",
    response_model=BenchmarkComparisonResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Compare multiple models against a dataset snapshot",
)
async def compare_models(
    payload: BenchmarkCompareRequest,
    db: AsyncSession = Depends(get_db),
) -> BenchmarkComparisonResponse:
    """Benchmark multiple models against the identical dataset snapshot and produce comparative metrics."""
    service = BenchmarkService(db)
    return await service.compare_models(payload)


@benchmarks_router.get(
    "/{comparison_id}",
    response_model=BenchmarkComparisonResponse,
    summary="Get benchmark comparison details and matrix",
)
async def get_comparison(
    comparison_id: str,
    db: AsyncSession = Depends(get_db),
) -> BenchmarkComparisonResponse:
    """Fetch comparative scorecard matrix, model results, and reproducibility hash."""
    service = BenchmarkService(db)
    return await service.get_comparison(comparison_id)
