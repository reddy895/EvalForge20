"""Provider, evaluator, and metric discovery endpoints."""

from typing import Any

from fastapi import APIRouter

from app.evaluators.registry import registry
from app.providers.registry import provider_registry

discovery_router = APIRouter(prefix="/v1", tags=["Discovery"])


@discovery_router.get("/providers", summary="List available model providers")
async def list_providers_endpoint() -> list[str]:
    """Return all registered model providers."""
    return provider_registry.list_providers()


@discovery_router.get("/metrics", summary="List registered evaluation metrics")
async def list_metrics_endpoint() -> list[dict[str, Any]]:
    """Return all registered metric definitions and their schemas."""
    return [m.model_dump() for m in registry.list_metrics()]


@discovery_router.get("/evaluators", summary="List active evaluators")
async def list_evaluators_endpoint() -> list[dict[str, Any]]:
    """Return active evaluators."""
    return [m.model_dump() for m in registry.list_metrics()]
