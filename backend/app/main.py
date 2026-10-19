"""Main FastAPI application entry point for EvalForge20."""

from contextlib import asynccontextmanager

from backend.app.api.routes.benchmarks import router as benchmarks_router
from backend.app.api.routes.comparisons import router as comparisons_router
from backend.app.api.routes.evaluations import router as evaluations_router
from backend.app.api.routes.health import router as health_router
from backend.app.api.routes.models import router as models_router
from backend.app.api.routes.ollama import router as ollama_router
from backend.app.api.routes.recommendations import router as recommendations_router
from backend.app.core.config import get_settings
from backend.app.core.errors import EvalForgeError
from backend.app.core.logging import get_logger, setup_logging
from backend.app.db.database import init_db
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

logger = get_logger("main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown events."""
    setup_logging()
    logger.info("Initializing EvalForge20 database schema...")
    init_db()
    logger.info("EvalForge20 backend operational.")
    yield
    logger.info("EvalForge20 backend shutdown.")


def create_app() -> FastAPI:
    """Build and configure the FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title="EvalForge20 API",
        description="Local-first LLM model intelligence and evaluation platform.",
        version=settings.app_version,
        lifespan=lifespan,
    )

    # CORS configuration
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            settings.frontend_origin,
            "http://localhost:5173",
            "http://127.0.0.1:5173",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Global Exception Handler
    @app.exception_handler(EvalForgeError)
    async def evalforge_error_handler(request: Request, exc: EvalForgeError):
        return JSONResponse(
            status_code=400,
            content={
                "error": exc.code.value,
                "message": exc.message,
                "details": exc.details,
            },
        )

    # Mount Route Modules
    app.include_router(health_router)
    app.include_router(models_router)
    app.include_router(ollama_router)
    app.include_router(benchmarks_router)
    app.include_router(evaluations_router)
    app.include_router(recommendations_router)
    app.include_router(comparisons_router)

    return app


# Ensure database tables exist upon module loading
init_db()

app = create_app()

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("backend.app.main:app", host="127.0.0.1", port=8000, reload=True)
