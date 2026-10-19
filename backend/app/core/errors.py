"""Normalized domain errors and exceptions."""

from enum import StrEnum
from typing import Any


class ErrorCode(StrEnum):
    NOT_FOUND = "not_found"
    VALIDATION_ERROR = "validation_error"
    OLLAMA_UNREACHABLE = "ollama_unreachable"
    MODEL_NOT_FOUND = "model_not_found"
    INFERENCE_FAILED = "inference_failed"
    EVALUATION_ERROR = "evaluation_error"
    AUTHENTICATION_ERROR = "authentication_error"
    EXECUTION_TIMEOUT = "execution_timeout"


class EvalForgeError(Exception):
    """Base application exception."""

    def __init__(
        self, message: str, code: ErrorCode = ErrorCode.EVALUATION_ERROR, details: Any = None
    ):
        super().__init__(message)
        self.message = message
        self.code = code
        self.details = details
