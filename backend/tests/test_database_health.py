"""Unit tests for database health verification probe."""

import pytest

from src.evalforge.database.health import check_database_health


@pytest.mark.asyncio
async def test_database_health_check() -> None:
    health = await check_database_health()
    assert health["connected"] is True
    assert health["status"] == "healthy"
    assert health["backend"] == "sqlite"
