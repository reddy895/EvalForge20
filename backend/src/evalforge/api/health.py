"""Health check and system diagnostics endpoints."""

from datetime import UTC, datetime

from fastapi import APIRouter
from pydantic import BaseModel

from src.evalforge.core.config import get_settings
from src.evalforge.providers.ollama.client import get_ollama_client

health_router = APIRouter(tags=["Health"])


class HealthResponse(BaseModel):
    status: str
    app: str
    version: str
    environment: str
    timestamp: str
    ollama_base_url: str
    ollama_reachable: bool = False
    ollama_version: str | None = None
    ollama_installed_models: int = 0


@health_router.get("/health", response_model=HealthResponse)
async def check_health() -> HealthResponse:
    """Check application health status, local Ollama daemon connectivity, and models."""
    settings = get_settings()
    client = get_ollama_client()
    reachable = await client.check_health()
    version = None
    model_count = 0

    if reachable:
        try:
            version = await client.get_version()
        except Exception:
            version = "unknown"
        try:
            tags = await client.list_tags()
            model_count = len(tags.get("models", []))
        except Exception:
            model_count = 0

    return HealthResponse(
        status="healthy",
        app=settings.APP_NAME,
        version=settings.APP_VERSION,
        environment=settings.ENVIRONMENT,
        timestamp=datetime.now(UTC).isoformat(),
        ollama_base_url=settings.OLLAMA_BASE_URL,
        ollama_reachable=reachable,
        ollama_version=version,
        ollama_installed_models=model_count,
    )
