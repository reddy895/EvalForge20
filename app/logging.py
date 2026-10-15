"""Structured logging configuration for EvalForge20."""

import logging
import re
import sys
from typing import Any

from app.config import get_settings

# Patterns to redact from logs
SENSITIVE_PATTERNS = [
    re.compile(r"(?i)(api[_-]?key|secret|token|password|auth|bearer)\s*[:=]\s*['\"]?([a-zA-Z0-9_\-\.]{8,})['\"]?"),
    re.compile(r"(?i)(sk-[a-zA-Z0-9_\-]{20,})"),
    re.compile(r"(?i)(ls__[a-zA-Z0-9_\-]{20,})"),
]


class SecretRedactionFilter(logging.Filter):
    """Logging filter that redacts API keys and sensitive tokens."""

    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            record.msg = self.redact_text(record.msg)
        if record.args:
            if isinstance(record.args, dict):
                record.args = {k: self.redact_value(v) for k, v in record.args.items()}
            elif isinstance(record.args, tuple):
                record.args = tuple(self.redact_value(v) for v in record.args)
        return True

    @classmethod
    def redact_text(cls, text: str) -> str:
        for pattern in SENSITIVE_PATTERNS:
            text = pattern.sub(r"\1=[REDACTED]", text)
        return text

    @classmethod
    def redact_value(cls, val: Any) -> Any:
        if isinstance(val, str):
            return cls.redact_text(val)
        return val


def setup_logging(level: str | None = None) -> None:
    """Configure root logger with structured formatting and secret redaction."""
    settings = get_settings()
    log_level = level or settings.log_level.upper()

    numeric_level = getattr(logging, log_level, logging.INFO)

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(numeric_level)
    handler.addFilter(SecretRedactionFilter())

    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)

    # Avoid adding duplicate handlers on multiple calls
    root_logger.handlers = [handler]

    # Suppress verbose third-party logging
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Return a logger instance for the given module name."""
    return logging.getLogger(name)
