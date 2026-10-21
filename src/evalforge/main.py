"""FastAPI application factory and lifespan lifecycle coordination."""

import time
import uuid
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware

from src.evalforge.api.health import health_router
from src.evalforge.api.v1.router import api_v1_router
from src.evalforge.core.config import get_settings
from src.evalforge.core.errors import register_exception_handlers
from src.evalforge.core.logging import (
    get_logger,
    set_request_id,
    setup_logging,
)
from src.evalforge.storage.database import close_db, init_db

logger = get_logger("evalforge.app")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Coordinates startup and graceful shutdown sequences."""
    settings = get_settings()
    setup_logging(level=settings.LOG_LEVEL, log_format=settings.LOG_FORMAT)
    logger.info(
        "Starting %s v%s [Env: %s]",
        settings.APP_NAME,
        settings.APP_VERSION,
        settings.ENVIRONMENT,
    )
    logger.info("Local Ollama base URL: %s", settings.OLLAMA_BASE_URL)

    # Initialize database schemas
    await init_db()

    yield

    logger.info("Initiating graceful shutdown...")
    # Cleanly close database connection pools and client sessions
    try:
        from src.evalforge.providers.ollama.client import close_ollama_client
        await close_ollama_client()
    except Exception as exc:
        logger.warning("Error closing provider clients: %s", exc)

    await close_db()
    logger.info("%s shutdown complete.", settings.APP_NAME)


def create_app() -> FastAPI:
    """Build and configure the FastAPI application instance."""
    settings = get_settings()

    application = FastAPI(
        title="EvalForge20 API",
        description="Local-First LLM and AI Agent Evaluation Platform",
        version=settings.APP_VERSION,
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    # Configure CORS middleware
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Request ID and latency tracking middleware
    @application.middleware("http")
    async def request_context_middleware(request: Request, call_next: object) -> Response:
        req_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        set_request_id(req_id)
        start_time = time.perf_counter()

        response: Response = await call_next(request)  # type: ignore[operator]

        duration_ms = (time.perf_counter() - start_time) * 1000
        response.headers["X-Request-ID"] = req_id
        response.headers["X-Process-Time-Ms"] = f"{duration_ms:.2f}"
        return response

    # Register centralized exception handlers
    register_exception_handlers(application)

    # Register top-level endpoints
    application.include_router(health_router)
    application.include_router(api_v1_router, prefix="/api/v1")

    return application


app = create_app()
