"""Main API v1 router mounting all versioned sub-routers."""

from fastapi import APIRouter
from src.evalforge.api.v1.benchmarks import benchmarks_router
from src.evalforge.api.v1.datasets import datasets_router
from src.evalforge.api.v1.evaluations import evaluations_router
from src.evalforge.api.v1.providers import providers_router

api_v1_router = APIRouter()
api_v1_router.include_router(providers_router)
api_v1_router.include_router(datasets_router)
api_v1_router.include_router(evaluations_router)
api_v1_router.include_router(benchmarks_router)
