"""Modular API route for multi-provider registry and health details."""

from fastapi import APIRouter
from src.evalforge.providers.registry import get_provider_registry

router = APIRouter(prefix="/providers", tags=["providers"])

@router.get("")
def list_providers():
    registry = get_provider_registry()
    return {"providers": registry.list_names()}

@router.get("/details")
async def list_provider_details():
    registry = get_provider_registry()
    details = await registry.list_details()
    return {"total": len(details), "providers": details}
