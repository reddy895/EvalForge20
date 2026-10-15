"""Unit tests for configuration and logging."""

import logging

from app.config import get_settings
from app.logging import SecretRedactionFilter, setup_logging


def test_default_settings():
    """Verify default application settings."""
    settings = get_settings()
    assert settings.env == "testing"
    assert settings.max_concurrency >= 1
    assert not settings.is_langsmith_enabled
    assert settings.ollama_base_url.startswith("http")


def test_secret_redaction_filter():
    """Verify sensitive token redaction in logs."""
    text = "Authorization: Bearer sk-antigravity1234567890abcdef123456"
    redacted = SecretRedactionFilter.redact_text(text)
    assert "sk-antigravity" not in redacted
    assert "[REDACTED]" in redacted

    ls_text = "LangSmith key ls__9876543210fedcba987654"
    redacted_ls = SecretRedactionFilter.redact_text(ls_text)
    assert "ls__987654" not in redacted_ls
    assert "[REDACTED]" in redacted_ls


def test_setup_logging_no_crash():
    """Verify setup_logging executes without error."""
    setup_logging("DEBUG")
    logger = logging.getLogger("test_module")
    logger.debug("Debug logging works")
    logger.info("Info logging works")
