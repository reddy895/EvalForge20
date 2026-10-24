"""Dataset and TestCase specialized repository."""

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.evalforge.storage.models.dataset import Dataset, TestCase
from src.evalforge.storage.repositories.base import BaseRepository


class DatasetRepository(BaseRepository[Dataset]):
    """Specialized repository for Datasets and nested TestCases."""

    def __init__(self, session: AsyncSession):
        super().__init__(session=session, model_cls=Dataset)

    async def get_with_cases(self, dataset_id: str) -> Dataset | None:
        """Fetch a dataset eager-loading all its test cases by ID, name, or benchmark slug."""
        # 1. Try direct ID match
        stmt = (
            select(Dataset)
            .where(Dataset.id == dataset_id)
            .options(selectinload(Dataset.test_cases))
        )
        result = await self.session.execute(stmt)
        ds = result.scalar_one_or_none()
        if ds and ds.test_cases:
            return ds

        # 2. Try match by name or slug in tags
        stmt = (
            select(Dataset)
            .where(
                (Dataset.name == dataset_id)
                | (func.lower(Dataset.name) == func.lower(dataset_id))
                | (Dataset.tags_json.like(f"%{dataset_id}%"))
            )
            .options(selectinload(Dataset.test_cases))
        )
        result = await self.session.execute(stmt)
        ds = result.scalar_one_or_none()
        if ds and ds.test_cases:
            return ds

        # 3. Fast standard benchmark slug map
        slug_to_name: dict[str, str] = {
            "coding_basics": "Python Algorithmic Synthesis",
            "coding": "Python Algorithmic Synthesis",
            "structured_json": "Constrained JSON Schema Extraction",
            "json": "Constrained JSON Schema Extraction",
            "reasoning_math": "Mathematical Word Logic",
            "math": "Mathematical Word Logic",
            "rag_retrieval": "Needle-in-a-Haystack Fact Recall",
            "rag": "Needle-in-a-Haystack Fact Recall",
        }
        resolved_name = slug_to_name.get(dataset_id.lower())
        if resolved_name:
            stmt = (
                select(Dataset)
                .where(Dataset.name == resolved_name)
                .options(selectinload(Dataset.test_cases))
            )
            result = await self.session.execute(stmt)
            ds = result.scalar_one_or_none()
            if ds and ds.test_cases:
                return ds

        # 3. Seed standard evaluation benchmarks and check slug map
        try:
            from src.evalforge.datasets.seeder import seed_standard_datasets
            slug_map = await seed_standard_datasets(self.session)
            target_id = slug_map.get(dataset_id.lower())
            if target_id:
                stmt = (
                    select(Dataset)
                    .where(Dataset.id == target_id)
                    .options(selectinload(Dataset.test_cases))
                )
                result = await self.session.execute(stmt)
                return result.scalar_one_or_none()
        except Exception:
            pass

        return None

    async def get_by_name(self, name: str) -> Dataset | None:
        """Fetch dataset by exact name."""
        stmt = select(Dataset).where(Dataset.name == name)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_with_counts(self, offset: int = 0, limit: int = 50) -> list[tuple[Dataset, int]]:
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

    async def get_case(self, case_id: str) -> TestCase | None:
        """Retrieve individual test case."""
        return await self.session.get(TestCase, case_id)

    async def add_cases(self, dataset_id: str, cases: list[TestCase]) -> list[TestCase]:
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
