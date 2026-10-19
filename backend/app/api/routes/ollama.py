"""Ollama health, status, installed models, and pull endpoints."""

from backend.app.core.errors import ErrorCode, EvalForgeError
from backend.app.schemas.models import (
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
