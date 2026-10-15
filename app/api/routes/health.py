"""Health and system readiness endpoints."""

from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from app import __version__
from app.config import get_settings
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


@health_router.get("/ready", summary="System dependency readiness check")
async def readiness_check(db: Session = Depends(get_db)) -> dict[str, Any]:
    """Verify that database is responsive and registered providers are loaded."""
    settings = get_settings()

    # 1. Check DB connectivity
    try:
        db.execute(text("SELECT 1"))
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database connection error: {exc}",
        ) from exc

    return {
        "status": "ready",
        "database": "connected",
        "version": __version__,
        "environment": settings.env,
        "available_providers": provider_registry.list_providers(),
        "langsmith_enabled": settings.is_langsmith_enabled,
    }
