"""Modular API route for multi-provider registry, diagnostics, and model discovery."""

from typing import Any
from fastapi import APIRouter, Query

from src.evalforge.core.config import get_settings
from src.evalforge.providers.ollama.diagnostics import run_ollama_diagnostics
from src.evalforge.providers.registry import get_provider_registry

router = APIRouter(prefix="/providers", tags=["providers"])


@router.get("")
def list_providers() -> dict[str, Any]:
    registry = get_provider_registry()
    return {"providers": registry.list_names()}


@router.get("/details")
async def list_provider_details() -> dict[str, Any]:
    registry = get_provider_registry()
    details = await registry.list_details()
    return {"total": len(details), "providers": details}


@router.get("/ollama/health")
async def get_ollama_health_diagnostics(
    model: str | None = Query(None, description="Optional target model to verify readiness")
) -> dict[str, Any]:
    """Execute complete 8-state Ollama connectivity probe and actionable diagnostics."""
    settings = get_settings()
    report = await run_ollama_diagnostics(
        base_url=settings.OLLAMA_BASE_URL,
        requested_model=model,
    )
    return {
        "status": "healthy" if report.reachable else "unreachable",
        "base_url": report.base_url,
        "reachable": report.reachable,
        "connectivity_state": report.connectivity_state,
        "version": report.version,
        "installed_locally": report.installed_locally,
        "installed_models_count": report.installed_models_count,
        "available_models": report.available_models,
        "model_ready": report.model_ready,
        "suggestion": report.remediation_hint,
        "error_message": report.error_message,
        "last_checked_at": report.last_checked_at,
    }
