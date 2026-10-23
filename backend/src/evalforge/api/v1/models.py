"""API endpoints for model discovery, catalog inspection, and synchronization."""

from fastapi import APIRouter, Query, status
from pydantic import BaseModel

from src.evalforge.core.errors import ModelNotFoundError
from src.evalforge.providers.schemas import ModelInfo
from src.evalforge.services.model_service import ModelService

models_router = APIRouter(prefix="/models", tags=["Models"])


class ModelsListResponse(BaseModel):
    total: int
    offset: int
    limit: int
    models: list[ModelInfo]


class ModelRefreshResponse(BaseModel):
    success: bool
    total_models: int
    refreshed_at: str


@models_router.get("", response_model=ModelsListResponse, summary="List and filter catalog models")
async def list_models(
    query: str | None = Query(None, description="Search term for model name, provider, or task"),
    provider: str | None = Query(None, description="Filter by provider name"),
    task: str | None = Query(None, description="Filter by recommended task tag"),
    is_local: bool | None = Query(None, description="Filter by local execution capability"),
    is_installed: bool | None = Query(None, description="Filter by locally installed models"),
    supports_tools: bool | None = Query(None, description="Filter by tool calling support"),
    supports_structured_output: bool | None = Query(None, description="Filter by JSON schema support"),
    sort_by: str = Query("recommended", description="Sort by recommended, benchmark, context, ram, or name"),
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
) -> ModelsListResponse:
    """Retrieve catalog models with search, provider filtering, capabilities, and pagination."""
    items, total = await ModelService.filter_models(
        query=query,
        provider=provider,
        task=task,
        is_local=is_local,
        is_installed=is_installed,
        supports_tools=supports_tools,
        supports_structured_output=supports_structured_output,
        sort_by=sort_by,
        offset=offset,
        limit=limit,
    )
    return ModelsListResponse(total=total, offset=offset, limit=limit, models=items)


@models_router.get("/{model_id}", response_model=ModelInfo, summary="Get details for a specific model")
async def get_model(model_id: str) -> ModelInfo:
    """Retrieve full technical specifications, hardware requirements, pricing, and benchmarks for a model."""
    all_models = await ModelService.get_all_models()
    cleaned_id = model_id.removeprefix("ollama:")
    for m in all_models:
        if (
            m.id in (model_id, cleaned_id)
            or (m.model_identifier and m.model_identifier in (model_id, cleaned_id))
            or (m.id and m.id.endswith(cleaned_id))
        ):
            return m
    raise ModelNotFoundError(model_id, "catalog")


@models_router.post(
    "/refresh",
    response_model=ModelRefreshResponse,
    status_code=status.HTTP_200_OK,
    summary="Synchronize and discover models dynamically",
)
async def refresh_models() -> ModelRefreshResponse:
    """Trigger live synchronization against local Ollama daemon and configured cloud endpoints."""
    models = await ModelService.get_all_models(force_refresh=True)
    from datetime import UTC, datetime

    return ModelRefreshResponse(
        success=True,
        total_models=len(models),
        refreshed_at=datetime.now(UTC).isoformat(),
    )
