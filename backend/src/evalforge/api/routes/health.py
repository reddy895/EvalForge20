"""Modular API route for health and readiness probes."""

from fastapi import APIRouter

from src.evalforge.core.config import get_settings
from src.evalforge.database.health import check_database_health

router = APIRouter(prefix="/health", tags=["health"])

@router.get("")
async def health_probe():
    settings = get_settings()
    db_health = await check_database_health()
    return {
        "status": "healthy" if db_health.get("connected") else "degraded",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "database": db_health,
        "ollama_base_url": settings.OLLAMA_BASE_URL,
    }
