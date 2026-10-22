"""Generic asynchronous repository base class."""

import builtins
from typing import Generic, TypeVar

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.evalforge.core.errors import NotFoundError
from src.evalforge.storage.base import Base

ModelT = TypeVar("ModelT", bound=Base)


class BaseRepository(Generic[ModelT]):
    """Generic async CRUD repository."""

    def __init__(self, session: AsyncSession, model_cls: type[ModelT]):
        self.session = session
        self.model_cls = model_cls

    async def get(self, entity_id: str) -> ModelT | None:
        """Retrieve single entity by primary key."""
        result = await self.session.get(self.model_cls, entity_id)
        return result

    async def get_or_fail(self, entity_id: str, resource_name: str | None = None) -> ModelT:
        """Retrieve single entity or raise domain NotFoundError."""
        entity = await self.get(entity_id)
        if entity is None:
            name = resource_name or self.model_cls.__name__
            raise NotFoundError(resource=name, identifier=entity_id)
        return entity

    async def list(self, offset: int = 0, limit: int = 50) -> list[ModelT]:
        """List entities with pagination."""
        stmt = select(self.model_cls).offset(offset).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def count(self) -> int:
        """Count total entities in table."""
        stmt = select(func.count()).select_from(self.model_cls)
        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def add(self, entity: ModelT) -> ModelT:
        """Stage new entity in session."""
        self.session.add(entity)
        await self.session.flush()
        return entity

    async def add_all(self, entities: builtins.list[ModelT]) -> builtins.list[ModelT]:
        """Stage batch of entities."""
        self.session.add_all(entities)
        await self.session.flush()
        return entities

    async def delete(self, entity: ModelT) -> None:
        """Delete entity from session."""
        await self.session.delete(entity)
        await self.session.flush()

    async def flush(self) -> None:
        """Flush pending changes to the database transaction."""
        await self.session.flush()
