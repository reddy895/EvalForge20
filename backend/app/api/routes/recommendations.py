"""Task-suitability and hardware compatibility recommendation endpoints."""

from backend.app.schemas.recommendations import (
    HardwareProfileInput,
    TaskRecommendationRequest,
    TaskRecommendationResponse,
)
from backend.app.services.recommendation_service import RecommendationService
from fastapi import APIRouter

router = APIRouter(prefix="/v1/recommendations", tags=["Recommendations"])
service = RecommendationService()


@router.post("/task", response_model=TaskRecommendationResponse)
async def get_task_recommendations(req: TaskRecommendationRequest):
    """Calculate and explain ranked model recommendations for a specific AI task."""
    return await service.recommend_for_task(req)


@router.post("/hardware")
def get_hardware_recommendations(profile: HardwareProfileInput):
    """Analyze which models can run locally given system RAM, GPU, and VRAM limits."""
    return service.evaluate_hardware_compatibility(profile)
