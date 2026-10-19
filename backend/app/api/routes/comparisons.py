"""Multi-model side-by-side comparison endpoints."""

from backend.app.schemas.comparisons import (
    ModelComparisonRequest,
    ModelComparisonResult,
)
from backend.app.services.comparison_service import ComparisonService
from fastapi import APIRouter

router = APIRouter(prefix="/v1/comparisons", tags=["Comparisons"])
comparison_service = ComparisonService()


@router.post("", response_model=ModelComparisonResult)
async def compare_models(req: ModelComparisonRequest):
    """Generate side-by-side comparative matrix across 2 to 4 models."""
    return await comparison_service.compare_models(req)
