"""API routers and endpoints for EvalForge20."""

from app.api.routes.catalog import catalog_router
from app.api.routes.comparisons import comparisons_router
from app.api.routes.evaluations import evaluations_router
from app.api.routes.health import health_router
from app.api.routes.ollama import ollama_router
from app.api.routes.reports import reports_router

__all__ = [
    "health_router",
    "evaluations_router",
    "ollama_router",
    "comparisons_router",
    "reports_router",
    "catalog_router",
]
