"""Ollama health, status, installed models, and pull endpoints."""

from backend.app.core.errors import ErrorCode, EvalForgeError
from backend.app.schemas.models import (
    OllamaGenerateRequest,
    OllamaGenerateResponse,
    OllamaModelPullRequest,
    OllamaModelPullResponse,
    OllamaStatusReport,
)
from backend.app.services.ollama_service import OllamaService
from fastapi import APIRouter, HTTPException, status

router = APIRouter(prefix="/v1/ollama", tags=["Ollama"])
ollama_service = OllamaService()


@router.get("/status", response_model=OllamaStatusReport)
async def get_ollama_status():
    """Check connectivity to local Ollama daemon and discover installed models."""
    return await ollama_service.get_status()


@router.get("/models")
async def get_installed_models():
    """List all models currently installed and available for local inference."""
    status_report = await ollama_service.get_status()
    return {
        "is_reachable": status_report.is_reachable,
        "base_url": status_report.base_url,
        "status_label": status_report.status_label,
        "installed_models": status_report.installed_models,
        "models_count": status_report.models_count,
        "error_message": status_report.error_message,
    }


@router.post("/generate", response_model=OllamaGenerateResponse)
async def generate_completion(req: OllamaGenerateRequest):
    """Execute local model inference with accurate latency and token metrics."""
    try:
        res = await ollama_service.generate(
            model=req.model,
            prompt=req.prompt,
            temperature=req.temperature,
        )
        tokens = res.get("tokens", {})
        return OllamaGenerateResponse(
            model=req.model,
            output=res["output"],
            latency_ms=res["latency_ms"],
            prompt_tokens=tokens.get("prompt_tokens", 0),
            completion_tokens=tokens.get("completion_tokens", 0),
            total_tokens=tokens.get("total_tokens", 0),
            is_success=res.get("is_success", True),
        )
    except EvalForgeError as e:
        if e.code == ErrorCode.MODEL_NOT_FOUND:
            status_code = status.HTTP_404_NOT_FOUND
        elif e.code == ErrorCode.OLLAMA_UNREACHABLE:
            status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        elif e.code == ErrorCode.EXECUTION_TIMEOUT:
            status_code = status.HTTP_504_GATEWAY_TIMEOUT
        else:
            status_code = status.HTTP_502_BAD_GATEWAY
        raise HTTPException(status_code=status_code, detail=e.message) from None


@router.post("/pull", response_model=OllamaModelPullResponse, status_code=status.HTTP_202_ACCEPTED)
async def pull_model(req: OllamaModelPullRequest):
    """Initiate an explicit model download via local Ollama."""
    try:
        res = await ollama_service.pull_model(req.model)
        return OllamaModelPullResponse(
            model=res["model"],
            status=res["status"],
            message=res["message"],
        )
    except EvalForgeError as e:
        status_code = (
            status.HTTP_400_BAD_REQUEST
            if e.code == ErrorCode.VALIDATION_ERROR
            else status.HTTP_502_BAD_GATEWAY
        )
        raise HTTPException(status_code=status_code, detail=e.message) from None
