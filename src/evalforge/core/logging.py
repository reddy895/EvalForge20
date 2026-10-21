"""Structured logging with contextual tracking for request and evaluation IDs."""

import json
import logging
import sys
from contextvars import ContextVar
from datetime import datetime, timezone
from typing import Any, Dict, Optional

# Context variables for asynchronous request and evaluation tracing
request_id_ctx: ContextVar[Optional[str]] = ContextVar("request_id_ctx", default=None)
evaluation_id_ctx: ContextVar[Optional[str]] = ContextVar("evaluation_id_ctx", default=None)


def set_request_id(request_id: Optional[str]) -> None:
    request_id_ctx.set(request_id)


def get_request_id() -> Optional[str]:
    return request_id_ctx.get()


def set_evaluation_id(evaluation_id: Optional[str]) -> None:
    evaluation_id_ctx.set(evaluation_id)


def get_evaluation_id() -> Optional[str]:
    return evaluation_id_ctx.get()


class StructuredJsonFormatter(logging.Formatter):
    """Formats log records as serialized JSON dictionaries with contextual metadata."""

    def format(self, record: logging.LogRecord) -> str:
        log_payload: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        req_id = get_request_id()
        if req_id:
            log_payload["request_id"] = req_id

        eval_id = get_evaluation_id()
        if eval_id:
            log_payload["evaluation_id"] = eval_id

        if record.exc_info:
            log_payload["exception"] = self.formatException(record.exc_info)

        # Attach extra fields passed in kwargs
        for key, value in record.__dict__.items():
            if key not in {
                "args", "asctime", "created", "exc_info", "exc_text", "filename",
                "funcName", "levelname", "levelno", "lineno", "module", "msecs",
                "message", "msg", "name", "pathname", "process", "processName",
                "relativeCreated", "stack_info", "thread", "threadName",
            }:
                log_payload[key] = value

        return json.dumps(log_payload, default=str)


class ConsoleFormatter(logging.Formatter):
    """Clean colorized console formatter for local developer experience."""

    LEVEL_COLORS = {
        logging.DEBUG: "\033[36m",    # Cyan
        logging.INFO: "\033[32m",     # Green
        logging.WARNING: "\033[33m",  # Yellow
        logging.ERROR: "\033[31m",    # Red
        logging.CRITICAL: "\033[35m", # Magenta
    }
    RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        color = self.LEVEL_COLORS.get(record.levelno, self.RESET)
        time_str = datetime.now(timezone.utc).strftime("%H:%M:%S")
        prefix = f"[{time_str}] {color}{record.levelname:<8}{self.RESET} [{record.name}]"
        
        ctx = []
        req_id = get_request_id()
        if req_id:
            ctx.append(f"req={req_id[:8]}")
        eval_id = get_evaluation_id()
        if eval_id:
            ctx.append(f"eval={eval_id[:8]}")
        ctx_str = f" ({' '.join(ctx)})" if ctx else ""

        message = f"{prefix}{ctx_str}: {record.getMessage()}"
        if record.exc_info:
            message += f"\n{self.formatException(record.exc_info)}"
        return message


def setup_logging(level: str = "INFO", log_format: str = "json") -> None:
    """Configure root logger with the specified format and severity level."""
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)

    # Remove existing handlers to avoid duplicates
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    console_handler = logging.StreamHandler(sys.stdout)
    if log_format.lower() == "console":
        console_handler.setFormatter(ConsoleFormatter())
    else:
        console_handler.setFormatter(StructuredJsonFormatter())

    root_logger.addHandler(console_handler)


def get_logger(name: str) -> logging.Logger:
    """Convenience getter for a named logger."""
    return logging.getLogger(name)
