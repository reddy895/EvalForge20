"""Async database session context manager, engine factory, and FastAPI dependency."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession

from src.evalforge.storage.database import (
    close_db,
    get_db,
    get_engine,
    get_session_factory,
    init_db,
)


@asynccontextmanager
async def get_db_context() -> AsyncGenerator[AsyncSession, None]:
    """Provide an async context manager yielding an AsyncSession."""
    factory = get_session_factory()
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


__all__ = [
    "get_db",
    "get_db_context",
    "init_db",
    "close_db",
    "get_engine",
    "get_session_factory",
]
