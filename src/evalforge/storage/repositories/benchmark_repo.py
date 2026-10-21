"""BenchmarkComparison repository for model comparisons and rankings."""

from typing import List, Optional
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.evalforge.storage.models.benchmark import BenchmarkComparison
from src.evalforge.storage.repositories.base import BaseRepository


class BenchmarkRepository(BaseRepository[BenchmarkComparison]):
    """Specialized repository for benchmark comparison aggregates."""

    def __init__(self, session: AsyncSession):
        super().__init__(session=session, model_cls=BenchmarkComparison)

    async def list_recent(
        self, offset: int = 0, limit: int = 20
    ) -> List[BenchmarkComparison]:
        """List benchmark comparisons in descending chronological order."""
        stmt = (
            select(BenchmarkComparison)
            .order_by(desc(BenchmarkComparison.created_at))
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_dataset(self, dataset_id: str) -> List[BenchmarkComparison]:
        """Fetch comparisons executed against a given dataset."""
        stmt = (
            select(BenchmarkComparison)
            .where(BenchmarkComparison.dataset_id == dataset_id)
            .order_by(desc(BenchmarkComparison.created_at))
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
