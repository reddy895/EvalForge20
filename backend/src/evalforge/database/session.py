"""Async database session context manager and dependencies."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import AsyncSession
from src.evalforge.storage.database import get_session_factory

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
