"""API endpoints for inference providers and local Ollama management."""

from typing import Any

from fastapi import APIRouter, Depends

from src.evalforge.core.config import Settings, get_settings
from src.evalforge.providers.registry import get_provider_registry
from src.evalforge.providers.schemas import InferenceRequest
from src.evalforge.schemas.providers import (
    OllamaHealthCheckResponse,
    OllamaModelsListResponse,
    OllamaTestInferenceRequest,
    OllamaTestInferenceResponse,
    ProvidersListResponse,
    ProviderStatusItem,
)

providers_router = APIRouter(prefix="/providers", tags=["Providers"])


@providers_router.get("", response_model=ProvidersListResponse)
async def list_providers() -> ProvidersListResponse:
    """List registered inference providers and their current availability."""
    registry = get_provider_registry()
    status_list = await registry.list_status()
    return ProvidersListResponse(
        providers=[
            ProviderStatusItem(
                name=item["name"],
                healthy=item["healthy"],
                default=item["default"],
            )
            for item in status_list
        ]
    )


@providers_router.get("/details", summary="Get comprehensive operational info for all providers")
async def list_provider_details() -> dict[str, Any]:
    """Return detailed metadata, configuration status, capabilities, and setup instructions."""
    registry = get_provider_registry()
    details = await registry.list_details()
    return {
        "total": len(details),
        "providers": [d.model_dump() for d in details],
    }


@providers_router.get("/{provider_name}", summary="Get operational info for a specific provider")
async def get_provider(provider_name: str) -> dict[str, Any]:
    """Return details and health for a single provider."""
    registry = get_provider_registry()
    provider = registry.get(provider_name)
    info = await provider.get_provider_info()
    return info.model_dump()


@providers_router.get("/ollama/health", response_model=OllamaHealthCheckResponse)
async def check_ollama_health(
    model: str | None = None,
    settings: Settings = Depends(get_settings),
) -> OllamaHealthCheckResponse:
    """Check connectivity to the local Ollama daemon, probe version, and test model readiness."""
    from src.evalforge.providers.ollama.diagnostics import run_ollama_diagnostics

    diag = await run_ollama_diagnostics(
        base_url=settings.OLLAMA_BASE_URL,
        requested_model=model,
    )

    return OllamaHealthCheckResponse(
        status="healthy" if diag.reachable else "unreachable",
        base_url=diag.base_url,
        reachable=diag.reachable,
        connectivity_state=diag.connectivity_state,
        version=diag.version,
        installed_locally=diag.installed_locally,
        installed_models_count=diag.installed_models_count,
        available_models=diag.available_models,
        model_ready=diag.model_ready,
        suggestion=diag.remediation_hint,
        last_checked_at=diag.last_checked_at,
    )


@providers_router.get("/ollama/models", response_model=OllamaModelsListResponse)
async def list_ollama_models() -> OllamaModelsListResponse:
    """List all models installed locally in the Ollama instance."""
    registry = get_provider_registry()
    provider = registry.get("ollama")
    models = await provider.list_models()
    return OllamaModelsListResponse(total=len(models), models=models)


@providers_router.post("/ollama/test", response_model=OllamaTestInferenceResponse)
async def test_ollama_model(
    request: OllamaTestInferenceRequest,
) -> OllamaTestInferenceResponse:
    """Execute a single test inference request against a specified local Ollama model."""
    registry = get_provider_registry()
    provider = registry.get("ollama")

    inference_req = InferenceRequest(
        model=request.model,
        prompt=request.prompt,
        temperature=request.temperature,
        system_prompt=request.system_prompt,
    )

    result = await provider.generate(inference_req)
    return OllamaTestInferenceResponse(
        success=True,
        model=result.model,
        text=result.text,
        latency_ms=result.latency_ms,
        usage=result.usage,
        raw_metadata=result.raw_metadata,
    )
