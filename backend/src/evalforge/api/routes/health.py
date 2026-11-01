"""Modular API route for health and readiness probes, and Ollama status."""

from typing import Any
from fastapi import APIRouter

from src.evalforge.core.config import get_settings
from src.evalforge.database.health import check_database_health
from src.evalforge.hardware.monitor import get_hardware_monitor
from src.evalforge.providers.ollama import get_ollama_provider

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_probe() -> dict[str, Any]:
    settings = get_settings()
    db_health = await check_database_health()
    hw_specs = get_hardware_monitor().get_system_specs()
    ollama_provider = get_ollama_provider()
    ollama_ok = await ollama_provider.health_check()

    return {
        "status": "healthy" if db_health.get("connected") else "degraded",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "database": db_health,
        "ollama": {
            "status": "connected" if ollama_ok else "unreachable",
            "base_url": settings.OLLAMA_BASE_URL,
        },
        "hardware": hw_specs,
    }


@router.get("/ollama/status")
async def ollama_status() -> dict[str, Any]:
    settings = get_settings()
    provider = get_ollama_provider()
    is_healthy = await provider.health_check()

    installed_models = []
    if is_healthy:
        try:
            models = await provider.list_models()
            installed_models = [m.model_dump() for m in models]
        except Exception:
            pass

    return {
        "status": "connected" if is_healthy else "unreachable",
        "base_url": settings.OLLAMA_BASE_URL,
        "is_healthy": is_healthy,
        "installed_models_count": len(installed_models),
        "models": installed_models,
    }
