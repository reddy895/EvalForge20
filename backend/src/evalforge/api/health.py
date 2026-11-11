"""Health check and system diagnostics endpoints."""

from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

from src.evalforge.core.config import get_settings
from src.evalforge.database.health import check_database_health
from src.evalforge.providers.ollama.client import get_ollama_client

health_router = APIRouter(tags=["Health"])


class HealthResponse(BaseModel):
    status: str
    app: str
    version: str
    environment: str
    timestamp: str
    api_ready: bool = True
    database_connected: bool = True
    ollama_base_url: str
    ollama_reachable: bool = False
    ollama_version: str | None = None
    ollama_installed_models: int = 0


class ReadinessResponse(BaseModel):
    status: str
    api_ready: bool = True
    database_connected: bool = True
    timestamp: str
    providers_online: dict[str, bool]


@health_router.get("/health", response_model=HealthResponse)
async def check_health() -> HealthResponse:
    """Check application health status, reporting API health independently of local Ollama connectivity."""
    import asyncio
    settings = get_settings()
    client = get_ollama_client()
    db_health = await check_database_health()
    reachable = False
    version = None
    model_count = 0

    try:
        reachable = await asyncio.wait_for(client.check_health(), timeout=1.5)
        if reachable:
            try:
                version = await asyncio.wait_for(client.get_version(), timeout=1.5)
            except Exception:
                version = "unknown"
            try:
                tags = await asyncio.wait_for(client.list_tags(), timeout=1.5)
                model_count = len(tags.get("models", []))
            except Exception:
                model_count = 0
    except Exception:
        reachable = False

    return HealthResponse(
        status="healthy" if db_health.get("connected") else "degraded",
        app=settings.APP_NAME,
        version=settings.APP_VERSION,
        environment=settings.ENVIRONMENT,
        timestamp=datetime.now(UTC).isoformat(),
        api_ready=True,
        database_connected=bool(db_health.get("connected")),
        ollama_base_url=settings.OLLAMA_BASE_URL,
        ollama_reachable=reachable,
        ollama_version=version,
        ollama_installed_models=model_count,
    )


@health_router.get("/health/backend")
async def check_backend_only_health() -> dict[str, Any]:
    """Pure backend health check completely decoupled from provider availability."""
    settings = get_settings()
    db_health = await check_database_health()
    return {
        "status": "healthy" if db_health.get("connected") else "degraded",
        "api_ready": True,
        "database_connected": bool(db_health.get("connected")),
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "timestamp": datetime.now(UTC).isoformat(),
    }



@health_router.get("/health/ready", response_model=ReadinessResponse)
async def check_readiness() -> ReadinessResponse:
    """Report API server readiness separately from external model-provider availability."""
    client = get_ollama_client()
    try:
        ollama_online = await client.check_health()
    except Exception:
        ollama_online = False
    db_health = await check_database_health()

    return ReadinessResponse(
        status="ready" if db_health.get("connected") else "not_ready",
        api_ready=True,
        database_connected=bool(db_health.get("connected")),
        timestamp=datetime.now(UTC).isoformat(),
        providers_online={"ollama": ollama_online, "mock": True},
    )


@health_router.get("/health/live")
async def check_liveness() -> dict[str, str]:
    """Lightweight liveness probe confirming HTTP event loop responsiveness."""
    return {"status": "alive", "timestamp": datetime.now(UTC).isoformat()}
