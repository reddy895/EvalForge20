"""API endpoints for unified model catalog and pricing lookup."""

from fastapi import APIRouter, Query

from app.catalog.models import CatalogModel, CatalogProviderInfo
from app.catalog.service import catalog_service

catalog_router = APIRouter(prefix="/v1/catalog", tags=["Catalog"])


@catalog_router.get("/models", response_model=list[CatalogModel], summary="List catalog models")
async def list_catalog_models(
    search: str | None = Query(
        default=None, description="Search term for model name or identifier"
    ),
    provider: str | None = Query(default=None, description="Filter by provider family"),
    is_local: bool | None = Query(default=None, description="Filter local vs cloud models"),
    capability: str | None = Query(default=None, description="Filter by task capability"),
) -> list[CatalogModel]:
    """Retrieve verified and discovered model entries with pricing and capabilities."""
    return await catalog_service.get_all_models(
        search=search,
        provider=provider,
        is_local=is_local,
        capability=capability,
    )


@catalog_router.get(
    "/models/{provider}/{model_identifier:path}",
    response_model=CatalogModel,
    summary="Get model details",
)
async def get_model_details(provider: str, model_identifier: str) -> CatalogModel:
    """Retrieve metadata, verified pricing, and capabilities for a specific model."""
    model = await catalog_service.get_model(provider=provider, model_identifier=model_identifier)
    return model


@catalog_router.get(
    "/providers", response_model=list[CatalogProviderInfo], summary="List catalog providers"
)
async def list_catalog_providers() -> list[CatalogProviderInfo]:
    """Retrieve status, connectivity, and model counts for all supported provider families."""
    return await catalog_service.get_provider_summaries()


@catalog_router.post("/custom", response_model=CatalogModel, summary="Register custom model")
async def register_custom_model(model: CatalogModel) -> CatalogModel:
    """Register or customize a model identifier in the local session catalog."""
    catalog_service.register_custom_model(model)
    return model
