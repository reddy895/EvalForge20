"""Domain error hierarchy and centralized FastAPI exception handlers."""

from typing import Any, Dict, Optional
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from src.evalforge.core.logging import get_logger, get_request_id

logger = get_logger("evalforge.errors")


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: Optional[Any] = None
    request_id: Optional[str] = None


class ErrorResponse(BaseModel):
    error: ErrorDetail


class EvalForgeError(Exception):
    """Base domain exception for EvalForge20."""

    def __init__(
        self,
        message: str,
        code: str = "INTERNAL_ERROR",
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: Optional[Any] = None,
    ):
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details


class NotFoundError(EvalForgeError):
    def __init__(self, resource: str, identifier: str):
        super().__init__(
            message=f"{resource} with identifier '{identifier}' was not found.",
            code="RESOURCE_NOT_FOUND",
            status_code=status.HTTP_404_NOT_FOUND,
            details={"resource": resource, "identifier": identifier},
        )


class EntityConflictError(EvalForgeError):
    def __init__(self, message: str, details: Optional[Any] = None):
        super().__init__(
            message=message,
            code="CONFLICT",
            status_code=status.HTTP_409_CONFLICT,
            details=details,
        )


class DataValidationError(EvalForgeError):
    def __init__(self, message: str, details: Optional[Any] = None):
        super().__init__(
            message=message,
            code="VALIDATION_FAILED",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details=details,
        )


class ProviderError(EvalForgeError):
    def __init__(self, message: str, provider: str, details: Optional[Any] = None):
        super().__init__(
            message=message,
            code="PROVIDER_ERROR",
            status_code=status.HTTP_502_BAD_GATEWAY,
            details={"provider": provider, "info": details},
        )


class ProviderConnectionError(ProviderError):
    def __init__(self, message: str, provider: str, base_url: str):
        super().__init__(
            message=message,
            provider=provider,
            details={
                "base_url": base_url,
                "suggestion": f"Check if {provider} is running at {base_url}. For Ollama, run 'ollama serve'.",
            },
        )
        self.code = "PROVIDER_UNAVAILABLE"
        self.status_code = status.HTTP_503_SERVICE_UNAVAILABLE


class ModelNotFoundError(ProviderError):
    def __init__(self, model_name: str, provider: str):
        super().__init__(
            message=f"Model '{model_name}' is not installed in {provider}.",
            provider=provider,
            details={
                "model": model_name,
                "suggestion": f"Run 'ollama pull {model_name}' to download this model locally.",
            },
        )
        self.code = "MODEL_NOT_FOUND"
        self.status_code = status.HTTP_404_NOT_FOUND


class EvaluationCancelledError(EvalForgeError):
    def __init__(self, evaluation_id: str):
        super().__init__(
            message=f"Evaluation '{evaluation_id}' was cancelled by the user.",
            code="EVALUATION_CANCELLED",
            status_code=status.HTTP_400_BAD_REQUEST,
            details={"evaluation_id": evaluation_id},
        )


class SecurityViolationError(EvalForgeError):
    def __init__(self, message: str, details: Optional[Any] = None):
        super().__init__(
            message=message,
            code="SECURITY_VIOLATION",
            status_code=status.HTTP_403_FORBIDDEN,
            details=details,
        )


class PayloadTooLargeError(EvalForgeError):
    def __init__(self, message: str, max_bytes: int):
        status_code = getattr(status, "HTTP_413_CONTENT_TOO_LARGE", 413)
        super().__init__(
            message=message,
            code="PAYLOAD_TOO_LARGE",
            status_code=status_code,
            details={"max_allowed_bytes": max_bytes},
        )


async def evalforge_exception_handler(_: Request, exc: EvalForgeError) -> JSONResponse:
    """Format known domain exceptions into consistent API responses."""
    req_id = get_request_id()
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message,
                "details": exc.details,
                "request_id": req_id,
            }
        },
    )


async def validation_exception_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
    """Format FastAPI / Pydantic validation errors."""
    req_id = get_request_id()
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": {
                "code": "REQUEST_VALIDATION_ERROR",
                "message": "The request body or parameters failed validation.",
                "details": exc.errors(),
                "request_id": req_id,
            }
        },
    )


async def unhandled_exception_handler(_: Request, exc: Exception) -> JSONResponse:
    """Catch unhandled errors without leaking sensitive system details to clients."""
    req_id = get_request_id()
    logger.exception("Unhandled server exception: %s", str(exc))
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected server error occurred. Please consult server logs.",
                "details": None,
                "request_id": req_id,
            }
        },
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Register all centralized exception handlers onto the FastAPI application."""
    app.add_exception_handler(EvalForgeError, evalforge_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)
