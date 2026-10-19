"""System liveness and readiness health endpoints."""

from backend.app.core.config import get_settings
from backend.app.services.ollama_service import OllamaService
from fastapi import APIRouter

router = APIRouter(tags=["Health"])


@router.get("/health")
async def health_check():
    """Liveness probe returning application operational status."""
    settings = get_settings()
    return {
        "status": "ok",
        "app": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
    }


@router.get("/ready")
async def readiness_check():
    """Readiness probe verifying Ollama connectivity and configuration."""
    settings = get_settings()
    ollama = OllamaService()
    status = await ollama.get_status()
    return {
        "status": "ready",
        "app": settings.app_name,
        "ollama": {
            "reachable": status.is_reachable,
            "status_label": status.status_label,
            "models_count": status.models_count,
        },
    }
