"""Aggregated router combining all modular API routes for EvalForge20."""

from fastapi import APIRouter

from src.evalforge.api.routes.benchmarks import router as benchmarks_router
from src.evalforge.api.routes.datasets import router as datasets_router
from src.evalforge.api.routes.evaluators import router as evaluators_router
from src.evalforge.api.routes.executions import router as executions_router
from src.evalforge.api.routes.experiments import router as experiments_router
from src.evalforge.api.routes.health import router as health_router
from src.evalforge.api.routes.leaderboard import router as leaderboard_router
from src.evalforge.api.routes.models import router as models_router
from src.evalforge.api.routes.providers import router as providers_router
from src.evalforge.api.routes.workflows import router as workflows_router

api_router = APIRouter()

api_router.include_router(health_router)
api_router.include_router(providers_router)
api_router.include_router(models_router)
api_router.include_router(workflows_router)
api_router.include_router(datasets_router)
api_router.include_router(evaluators_router)
api_router.include_router(executions_router)
api_router.include_router(experiments_router)
api_router.include_router(benchmarks_router)
api_router.include_router(leaderboard_router)

__all__ = ["api_router"]
