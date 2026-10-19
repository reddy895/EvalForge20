"""Model discovery, search, filtering, and profile retrieval routes."""

from backend.app.schemas.models import ModelProfile, ModelSummary
from backend.app.services.model_catalog import ModelCatalogService
from fastapi import APIRouter, HTTPException, Query, status

router = APIRouter(prefix="/v1/models", tags=["Models"])
catalog_service = ModelCatalogService()


@router.get("", response_model=list[ModelSummary])
async def list_models(
    query: str | None = Query(None, description="Search term for model name or capability"),
    provider: str | None = Query(None, description="Filter by provider (e.g. 'Meta', 'Qwen')"),
    task: str | None = Query(
        None, description="Filter by recommended task (e.g. 'coding', 'reasoning')"
    ),
    is_local: bool | None = Query(None, description="Filter for local Ollama-compatible models"),
    is_installed: bool | None = Query(
        None, description="Filter for currently installed local models"
    ),
    sort_by: str = Query(
        "recommended", description="Sort order: 'recommended', 'benchmark', 'context', 'ram'"
    ),
):
    """Retrieve catalog models with search, filtering, and live installation status."""
    return await catalog_service.list_models(
        query=query,
        provider=provider,
        task=task,
        is_local=is_local,
        is_installed=is_installed,
        sort_by=sort_by,
    )


@router.get("/{model_id}", response_model=ModelProfile)
async def get_model_profile(model_id: str):
    """Fetch complete model intelligence profile including benchmarks and hardware specs."""
    profile = await catalog_service.get_model_profile(model_id)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Model '{model_id}' was not found in catalog or local daemon.",
        )
    return profile
