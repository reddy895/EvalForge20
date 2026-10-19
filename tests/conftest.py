"""Global pytest fixtures for EvalForge20."""

from collections.abc import Generator
from pathlib import Path

import pytest
from backend.app.core.config import get_settings
from backend.app.db.database import init_db


@pytest.fixture(autouse=True)
def clean_environment(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> Generator[None, None, None]:
    """Isolate environment variables and use temporary database for all tests."""
    test_db = tmp_path / "test_evalforge20.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{test_db}")

    get_settings.cache_clear()
    init_db()
    yield
    get_settings.cache_clear()
