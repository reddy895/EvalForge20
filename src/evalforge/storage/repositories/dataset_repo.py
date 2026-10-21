"""Dataset and TestCase specialized repository."""

from typing import List, Optional, Tuple
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.evalforge.storage.models.dataset import Dataset, TestCase
from src.evalforge.storage.repositories.base import BaseRepository


class DatasetRepository(BaseRepository[Dataset]):
    """Specialized repository for Datasets and nested TestCases."""

    def __init__(self, session: AsyncSession):
        super().__init__(session=session, model_cls=Dataset)

    async def get_with_cases(self, dataset_id: str) -> Optional[Dataset]:
        """Fetch a dataset eager-loading all its test cases."""
        stmt = (
            select(Dataset)
            .where(Dataset.id == dataset_id)
            .options(selectinload(Dataset.test_cases))
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_name(self, name: str) -> Optional[Dataset]:
        """Fetch dataset by exact name."""
        stmt = select(Dataset).where(Dataset.name == name)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_with_counts(
        self, offset: int = 0, limit: int = 50
    ) -> List[Tuple[Dataset, int]]:
        """List datasets paired with their computed test case count."""
        stmt = (
            select(Dataset, func.count(TestCase.id).label("case_count"))
            .outerjoin(TestCase, TestCase.dataset_id == Dataset.id)
            .group_by(Dataset.id)
            .order_by(Dataset.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return [(row[0], row[1]) for row in result.all()]

    async def get_case(self, case_id: str) -> Optional[TestCase]:
        """Retrieve individual test case."""
        return await self.session.get(TestCase, case_id)

    async def add_cases(self, dataset_id: str, cases: List[TestCase]) -> List[TestCase]:
        """Batch insert test cases into a dataset."""
        for case in cases:
            case.dataset_id = dataset_id
            self.session.add(case)
        await self.session.flush()
        return cases

    async def delete_case(self, case_id: str) -> bool:
        """Delete an individual test case."""
        case = await self.get_case(case_id)
        if case:
            await self.session.delete(case)
            await self.session.flush()
            return True
        return False
