"""Normalized error categories, domain exceptions, and classification logic."""

import asyncio
from enum import Enum
from typing import Any


class NormalizedErrorCategory(str, Enum):
    """Standardized error categories across all providers and evaluators."""

    TIMEOUT = "timeout"
    PROVIDER_UNAVAILABLE = "provider_unavailable"
    AUTHENTICATION_ERROR = "authentication_error"
    RATE_LIMIT = "rate_limit"
    CONTEXT_LENGTH_EXCEEDED = "context_length_exceeded"
    INVALID_RESPONSE = "invalid_response"
    VALIDATION_ERROR = "validation_error"
    EXECUTION_ERROR = "execution_error"
    CANCELLED = "cancelled"


class EvalForgeError(Exception):
    """Base exception for all EvalForge20 operational errors."""

    def __init__(self, message: str, details: dict[str, Any] | None = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class DatasetValidationError(EvalForgeError):
    """Raised when a dataset fails schema or integrity validation."""

    def __init__(
        self,
        message: str,
        line_number: int | None = None,
        case_id: str | None = None,
        errors: list[str] | None = None,
    ):
        super().__init__(message, {"line": line_number, "case_id": case_id, "errors": errors or []})
        self.line_number = line_number
        self.case_id = case_id
        self.errors = errors or []


class ProviderError(EvalForgeError):
    """Raised when an external or local model provider encounters an error."""

    def __init__(
        self,
        message: str,
        category: NormalizedErrorCategory = NormalizedErrorCategory.EXECUTION_ERROR,
        status_code: int | None = None,
        raw_error: str | None = None,
    ):
        super().__init__(
            message,
            {"category": category.value, "status_code": status_code, "raw_error": raw_error},
        )
        self.category = category
        self.status_code = status_code
        self.raw_error = raw_error


class EvaluatorError(EvalForgeError):
    """Raised when an evaluator fails during evaluation."""

    def __init__(self, message: str, metric_id: str):
        super().__init__(message, {"metric_id": metric_id})
        self.metric_id = metric_id


class RunExecutionError(EvalForgeError):
    """Raised when an evaluation run fails unrecoverably."""

    pass


class ComparisonIncompatibleError(EvalForgeError):
    """Raised when attempting to compare incompatible evaluation runs."""

    pass


def classify_exception(exc: Exception) -> tuple[NormalizedErrorCategory, str]:
    """Classify an arbitrary exception into a normalized error category and message."""
    if isinstance(exc, asyncio.TimeoutError | TimeoutError):
        return NormalizedErrorCategory.TIMEOUT, f"Operation timed out: {exc!s}"

    if isinstance(exc, ProviderError):
        return exc.category, exc.message

    msg = str(exc).lower()
    if "connection refused" in msg or "connecterror" in msg or "failed to connect" in msg:
        return NormalizedErrorCategory.PROVIDER_UNAVAILABLE, str(exc)
    if "401" in msg or "403" in msg or "unauthorized" in msg or "forbidden" in msg:
        return NormalizedErrorCategory.AUTHENTICATION_ERROR, str(exc)
    if "429" in msg or "rate limit" in msg or "too many requests" in msg:
        return NormalizedErrorCategory.RATE_LIMIT, str(exc)
    if "context length" in msg or "maximum context" in msg or "too long" in msg:
        return NormalizedErrorCategory.CONTEXT_LENGTH_EXCEEDED, str(exc)
    if isinstance(exc, asyncio.CancelledError):
        return NormalizedErrorCategory.CANCELLED, "Operation was cancelled"

    return NormalizedErrorCategory.EXECUTION_ERROR, str(exc)
