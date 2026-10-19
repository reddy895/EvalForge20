"""API routes package for EvalForge20."""

from backend.app.api.routes.benchmarks import router as benchmarks_router
from backend.app.api.routes.comparisons import router as comparisons_router
from backend.app.api.routes.evaluations import router as evaluations_router
from backend.app.api.routes.health import router as health_router
from backend.app.api.routes.models import router as models_router
from backend.app.api.routes.ollama import router as ollama_router
from backend.app.api.routes.recommendations import router as recommendations_router

__all__ = [
    "health_router",
    "models_router",
    "ollama_router",
    "benchmarks_router",
    "evaluations_router",
    "recommendations_router",
    "comparisons_router",
]
