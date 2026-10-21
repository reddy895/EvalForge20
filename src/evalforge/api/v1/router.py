"""Main API v1 router mounting all versioned sub-routers."""

from fastapi import APIRouter
from src.evalforge.api.v1.providers import providers_router

api_v1_router = APIRouter()
api_v1_router.include_router(providers_router)
