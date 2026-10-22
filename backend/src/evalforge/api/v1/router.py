"""Main API v1 router mounting all versioned sub-routers."""

from fastapi import APIRouter

from src.evalforge.api.v1.agents import agents_alias_router, agents_router
from src.evalforge.api.v1.analytics import analytics_router
from src.evalforge.api.v1.benchmarks import benchmarks_router
from src.evalforge.api.v1.datasets import datasets_router
from src.evalforge.api.v1.evaluations import evaluations_router
from src.evalforge.api.v1.experiments import experiments_router
from src.evalforge.api.v1.models import models_router
from src.evalforge.api.v1.providers import providers_router
from src.evalforge.api.v1.rag import rag_router

api_v1_router = APIRouter()
api_v1_router.include_router(providers_router)
api_v1_router.include_router(models_router)
api_v1_router.include_router(datasets_router)
api_v1_router.include_router(evaluations_router)
api_v1_router.include_router(benchmarks_router)
api_v1_router.include_router(experiments_router)
api_v1_router.include_router(agents_router)
api_v1_router.include_router(agents_alias_router)
api_v1_router.include_router(analytics_router)
api_v1_router.include_router(rag_router)
