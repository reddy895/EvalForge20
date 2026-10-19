"""Structured logging for EvalForge20."""

import logging
import sys


def setup_logging(level: str = "INFO") -> None:
    """Initialize logging format and level."""
    log_format = "%(asctime)s [%(levelname)s] [%(name)s] %(message)s"
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format=log_format,
        handlers=[logging.StreamHandler(sys.stdout)],
    )


def get_logger(name: str) -> logging.Logger:
    """Return configured logger instance for a given module name."""
    return logging.getLogger(f"evalforge20.{name}")
