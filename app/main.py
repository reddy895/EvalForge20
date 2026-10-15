"""FastAPI main application entrypoint for EvalForge20."""

from contextlib import asynccontextmanager
from typing import Any
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from app import __version__
from app.api.routes.health import health_router
from app.domain.errors import EvalForgeError
from app.logging import get_logger, setup_logging
from app.storage.database import init_db

logger = get_logger("evalforge20.api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context for startup and shutdown initialization."""
    setup_logging()
    logger.info("Initializing EvalForge20 database schema...")
    init_db()
    logger.info("EvalForge20 backend successfully initialized.")
    yield


app = FastAPI(
    title="EvalForge20 API",
    description="Production-minded, local-first platform for evaluating, benchmarking, and comparing LLMs and AI agents.",
    version=__version__,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Register routes
app.include_router(health_router)


@app.exception_handler(EvalForgeError)
async def evalforge_error_handler(request: Request, exc: EvalForgeError) -> JSONResponse:
    """Standardized error handler for domain exceptions."""
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "error": exc.__class__.__name__,
            "message": exc.message,
            "details": exc.details,
        },
    )
