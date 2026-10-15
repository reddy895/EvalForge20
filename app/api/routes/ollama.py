"""Ollama local status, diagnostics, and model discovery endpoints."""

from typing import Any

from fastapi import APIRouter

from app.config import get_settings
from app.providers.ollama import OllamaProvider
from app.providers.ollama_diagnostics import (
    OllamaDiagnosticReport,
    check_ollama_status,
)

ollama_router = APIRouter(prefix="/v1", tags=["Ollama"])


@ollama_router.get(
    "/ollama/status",
    response_model=OllamaDiagnosticReport,
    summary="Check Ollama local daemon status and diagnostics",
)
async def get_ollama_status_endpoint() -> OllamaDiagnosticReport:
    """Check connectivity to the local Ollama server and return diagnostic status."""
    settings = get_settings()
    return await check_ollama_status(base_url=settings.ollama_base_url)


@ollama_router.get(
    "/models",
    summary="List available local models from Ollama",
)
async def list_models_endpoint() -> list[dict[str, Any]]:
    """List detailed metadata for models installed on the local Ollama daemon."""
    settings = get_settings()
    provider = OllamaProvider(base_url=settings.ollama_base_url)
    return await provider.list_detailed_models()
