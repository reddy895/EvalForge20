"""Modular API route for model dynamic discovery and technical catalog."""

from fastapi import APIRouter, Query
from src.evalforge.services.model_service import get_model_service

router = APIRouter(prefix="/models", tags=["models"])

@router.get("")
async def list_models(
    query: str | None = None,
    provider: str | None = None,
    task: str | None = None,
    is_local: bool | None = None,
    limit: int = 50,
    offset: int = 0,
):
    service = get_model_service()
    models, total = await service.filter_models(
        query=query, provider=provider, task=task, is_local=is_local, limit=limit, offset=offset
    )
    return {"total": total, "models": models}

@router.get("/{model_id}")
async def get_model(model_id: str):
    service = get_model_service()
    model = await service.get_model_by_id(model_id)
    if not model:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail=f"Model '{model_id}' not found")
    return model

@router.post("/refresh")
async def refresh_models():
    service = get_model_service()
    models = await service.get_all_models(force_refresh=True)
    return {"success": True, "total_models": len(models)}
