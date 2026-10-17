"""FastAPI main application entrypoint for EvalForge20."""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app import __version__
from app.api.routes.catalog import catalog_router
from app.api.routes.comparisons import comparisons_router
from app.api.routes.datasets import dataset_router
from app.api.routes.evaluations import eval_router
from app.api.routes.health import health_router
from app.api.routes.integrations import integrations_router
from app.api.routes.ollama import ollama_router
from app.api.routes.providers import discovery_router
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

# Enable CORS for local developer tools and UI dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routes
app.include_router(health_router)
app.include_router(dataset_router)
app.include_router(eval_router)
app.include_router(discovery_router)
app.include_router(catalog_router)
app.include_router(ollama_router)
app.include_router(integrations_router)
app.include_router(comparisons_router)

# Serve production frontend single-page application if built
_frontend_dist = Path("frontend/dist")
if _frontend_dist.exists() and (_frontend_dist / "index.html").exists():
    _assets_dir = _frontend_dist / "assets"
    if _assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=_assets_dir), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_spa_frontend(full_path: str):
        # Exclude API endpoints, docs, and system probes
        if full_path.startswith(("v1/", "health", "ready", "docs", "redoc", "openapi.json")):
            raise HTTPException(status_code=404, detail="Not Found")
        target_file = _frontend_dist / full_path
        if target_file.is_file():
            return FileResponse(target_file)
        return FileResponse(_frontend_dist / "index.html")


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Format Pydantic request validation errors into a consistent structure."""
    errors = []
    for err in exc.errors():
        field_path = ".".join(str(p) for p in err.get("loc", []))
        errors.append(
            {
                "field": field_path,
                "message": err.get("msg"),
                "type": err.get("type"),
            }
        )
    return JSONResponse(
        status_code=422,
        content={
            "error": "RequestValidationError",
            "message": "Input request validation failed",
            "details": {"validation_errors": errors},
        },
    )


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


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Safely handle unexpected server exceptions without leaking internal secrets."""
    logger.error("Unhandled internal server exception: %s", exc, exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "InternalServerError",
            "message": "An unexpected server error occurred. Please consult backend logs.",
            "details": {},
        },
    )
