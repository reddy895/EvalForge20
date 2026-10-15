"""Global pytest fixtures for EvalForge20."""

from collections.abc import Generator
from pathlib import Path

import pytest

from app.config import get_settings


@pytest.fixture(autouse=True)
def clean_environment(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> Generator[None, None, None]:
    """Isolate environment variables and use temporary database for all tests."""
    test_db = tmp_path / "test_evalforge20.db"
    monkeypatch.setenv("EVALFORGE20_ENV", "testing")
    monkeypatch.setenv("EVALFORGE20_DATABASE_URL", f"sqlite:///{test_db}")
    monkeypatch.setenv("EVALFORGE20_DATA_DIR", str(tmp_path / "data"))
    monkeypatch.setenv("LANGSMITH_TRACING", "false")
    monkeypatch.delenv("LANGSMITH_API_KEY", raising=False)

    # Invalidate cached settings
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()
