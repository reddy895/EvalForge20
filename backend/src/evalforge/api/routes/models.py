"""Modular API route for model dynamic discovery and technical catalog."""

from typing import Any
from fastapi import APIRouter

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
    from datetime import datetime, timezone
    service = get_model_service()
    models = await service.get_all_models(force_refresh=True)
    return {
        "success": True,
        "total_models": len(models),
        "refreshed_at": datetime.now(timezone.utc).isoformat(),
    }


@router.post("/test-connection")
async def test_model_connection(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    from src.evalforge.providers.registry import get_provider_registry
    req_dict = payload or {}
    model_id = req_dict.get("model_identifier") or req_dict.get("model") or "qwen2.5:3b"
    prompt = req_dict.get("prompt") or "Hello, respond with 'OK'."

    registry = get_provider_registry()
    provider = registry.resolve_model_provider(model_id)

    res = await provider.test_connection(model_id, prompt=prompt)
    if isinstance(res, dict) and "success" not in res:
        res["success"] = res.get("status") == "connected"
    return res
