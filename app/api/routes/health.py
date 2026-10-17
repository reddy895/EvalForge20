"""Health and system readiness endpoints."""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from app import __version__
from app.api.schemas import SystemReadinessResponse
from app.config import get_settings
from app.providers.ollama_diagnostics import check_ollama_status
from app.providers.registry import provider_registry
from app.storage.database import get_db

health_router = APIRouter(tags=["System"])


@health_router.get("/health", summary="Basic service health probe")
async def health_check() -> dict[str, Any]:
    """Return process health and version."""
    settings = get_settings()
    return {
        "status": "ok",
        "version": __version__,
        "environment": settings.env,
    }


@health_router.get(
    "/ready",
    response_model=SystemReadinessResponse,
    summary="System dependency readiness check",
)
async def readiness_check(db: Session = Depends(get_db)) -> SystemReadinessResponse:
    """Verify that database is responsive and report provider status."""
    settings = get_settings()

    # 1. Check DB connectivity
    try:
        db.execute(text("SELECT 1"))
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database connection error: {exc}",
        ) from exc

    # 2. Check provider readiness states
    providers_status: dict[str, str] = {
        "mock": "online",
        "sqlite": "connected",
    }

    # Ollama local check (non-blocking, failure does not fail readiness)
    try:
        ollama_rep = await check_ollama_status(
            base_url=settings.ollama_base_url, timeout_seconds=1.5
        )
        providers_status["ollama"] = "online" if ollama_rep.is_reachable else "offline"
    except Exception:
        providers_status["ollama"] = "offline"

    # Cloud providers credential check
    providers_status["openai"] = "configured" if settings.openai_api_key else "unconfigured"
    providers_status["anthropic"] = "configured" if settings.anthropic_api_key else "unconfigured"
    providers_status["gemini"] = "configured" if settings.gemini_api_key else "unconfigured"
    providers_status["nvidia"] = "configured" if settings.nvidia_api_key else "unconfigured"
    providers_status["custom_openai"] = (
        "configured" if settings.custom_openai_base_url else "unconfigured"
    )

    return SystemReadinessResponse(
        status="ready",
        database="connected",
        version=__version__,
        environment=settings.env,
        available_providers=provider_registry.list_providers(),
        providers_status=providers_status,
        langsmith_enabled=settings.is_langsmith_enabled,
    )
