"""Ollama local status, diagnostics, and model discovery endpoints."""

from typing import Any

import httpx
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

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
    models = await provider.list_detailed_models()
    # Handle both Pydantic model instances and raw dicts (e.g. from test mocks)
    return [m.model_dump() if hasattr(m, "model_dump") else dict(m) for m in models]


class ModelPullRequest(BaseModel):
    """Request body for pulling (downloading) an Ollama model."""

    model: str = Field(..., description="Model tag to pull, e.g. 'qwen2.5:3b'")


class ModelPullResponse(BaseModel):
    """Response for an Ollama model pull request."""

    model: str
    status: str
    message: str


@ollama_router.post(
    "/ollama/models/pull",
    response_model=ModelPullResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Initiate download of an Ollama model",
)
async def pull_ollama_model(body: ModelPullRequest) -> ModelPullResponse:
    """
    Initiate a download of the specified Ollama model.

    This is an explicit user-initiated action. The model download can be several
    gigabytes depending on the chosen model. The endpoint returns immediately with
    202 Accepted and triggers the pull asynchronously. Monitor /v1/models to check
    when the model appears. Pull failures (model not found, disk full, etc.) are
    returned as error responses.
    """
    settings = get_settings()
    base_url = settings.ollama_base_url.rstrip("/")
    model_tag = body.model.strip()

    if not model_tag:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Model tag must not be empty.",
        )

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Trigger the pull — Ollama streams progress but we just fire-and-forget
            # to avoid blocking. The frontend should poll /v1/models to detect completion.
            resp = await client.post(
                f"{base_url}/api/pull",
                json={"name": model_tag, "stream": False},
                timeout=10.0,
            )
            if resp.status_code == 200:
                return ModelPullResponse(
                    model=model_tag,
                    status="initiated",
                    message=(
                        f"Pull of '{model_tag}' has been initiated. "
                        "Depending on model size this may take several minutes. "
                        "Poll GET /v1/models to confirm when the model is available."
                    ),
                )
            else:
                try:
                    err_body = resp.json()
                    err_msg = err_body.get("error", f"Ollama returned HTTP {resp.status_code}")
                except Exception:
                    err_msg = f"Ollama returned HTTP {resp.status_code}"
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=f"Model pull failed: {err_msg}",
                )
    except httpx.ConnectError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                f"Cannot connect to Ollama at {base_url}. "
                "Ensure Ollama is running before pulling models."
            ),
        ) from None
    except httpx.TimeoutException:
        # Timeout on the initial trigger is unusual — surface as gateway error
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail=(
                f"Ollama at {base_url} did not respond in time. "
                "The pull may still be running. Check 'ollama list' on the server."
            ),
        ) from None
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error initiating model pull: {exc}",
        ) from exc
