"""Health check and system diagnostics endpoints."""

from datetime import UTC, datetime

from fastapi import APIRouter
from pydantic import BaseModel

from src.evalforge.core.config import get_settings

health_router = APIRouter(tags=["Health"])


class HealthResponse(BaseModel):
    status: str
    app: str
    version: str
    environment: str
    timestamp: str
    ollama_base_url: str


@health_router.get("/health", response_model=HealthResponse)
async def check_health() -> HealthResponse:
    """Check application health status and current operational environment."""
    settings = get_settings()
    return HealthResponse(
        status="healthy",
        app=settings.APP_NAME,
        version=settings.APP_VERSION,
        environment=settings.ENVIRONMENT,
        timestamp=datetime.now(UTC).isoformat(),
        ollama_base_url=settings.OLLAMA_BASE_URL,
    )
