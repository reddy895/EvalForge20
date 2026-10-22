"""Dataset application service managing datasets, test cases, and imports."""

from sqlalchemy.ext.asyncio import AsyncSession

from src.evalforge.core.config import get_settings
from src.evalforge.core.errors import (
    DataValidationError,
    EntityConflictError,
    NotFoundError,
    PayloadTooLargeError,
)
from src.evalforge.datasets.importers.csv_importer import parse_csv_content
from src.evalforge.datasets.importers.jsonl import parse_jsonl_content
from src.evalforge.schemas.dataset import (
    DatasetCreate,
    DatasetImportResponse,
    DatasetUpdate,
    TestCaseCreate,
)
from src.evalforge.storage.models.dataset import Dataset, TestCase
from src.evalforge.storage.repositories.dataset_repo import DatasetRepository


class DatasetService:
    """Orchestrates dataset lifecycle, test-case authoring, and file ingestion."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = DatasetRepository(session)
        self.settings = get_settings()

    async def create_dataset(self, data: DatasetCreate) -> Dataset:
        """Create new dataset entity and optionally attach initial test cases."""
        existing = await self.repo.get_by_name(data.name)
        if existing:
            raise EntityConflictError(f"A dataset with name '{data.name}' already exists.")

        dataset = Dataset(
            name=data.name,
            description=data.description,
            version=1,
        )
        dataset.tags = data.tags
        await self.repo.add(dataset)

        if data.cases:
            if len(data.cases) > self.settings.MAX_CASES_PER_DATASET:
                raise PayloadTooLargeError(
                    f"Test cases count ({len(data.cases)}) exceeds maximum limit of {self.settings.MAX_CASES_PER_DATASET}",
                    max_bytes=self.settings.MAX_CASES_PER_DATASET,
                )

            orm_cases = []
            for item in data.cases:
                tc = TestCase(
                    dataset_id=dataset.id,
                    prompt=item.prompt,
                    expected_output=item.expected_output,
                    context=item.context,
                )
                tc.tags = item.tags
                tc.metadata_dict = item.metadata
                tc.evaluator_config = item.evaluator_config
                orm_cases.append(tc)
            await self.repo.add_cases(dataset.id, orm_cases)

        return dataset

    async def get_dataset(self, dataset_id: str) -> Dataset:
        """Retrieve dataset metadata or raise NotFoundError."""
        return await self.repo.get_or_fail(dataset_id, "Dataset")

    async def get_dataset_with_cases(self, dataset_id: str) -> Dataset:
        """Fetch dataset including all test cases."""
        dataset = await self.repo.get_with_cases(dataset_id)
        if dataset is None:
            raise NotFoundError("Dataset", dataset_id)
        return dataset

    async def list_datasets(
        self, offset: int = 0, limit: int = 50
    ) -> tuple[int, list[tuple[Dataset, int]]]:
        """Return total count and paginated datasets with their case count."""
        total = await self.repo.count()
        items = await self.repo.list_with_counts(offset=offset, limit=limit)
        return total, items

    async def update_dataset(self, dataset_id: str, data: DatasetUpdate) -> Dataset:
        """Update dataset metadata and increment version number."""
        dataset = await self.get_dataset(dataset_id)

        if data.name and data.name != dataset.name:
            conflict = await self.repo.get_by_name(data.name)
            if conflict and conflict.id != dataset_id:
                raise EntityConflictError(f"Dataset name '{data.name}' is already taken.")
            dataset.name = data.name

        if data.description is not None:
            dataset.description = data.description

        if data.tags is not None:
            dataset.tags = data.tags

        dataset.version += 1
        await self.repo.flush()
        return dataset

    async def delete_dataset(self, dataset_id: str) -> None:
        """Delete dataset and cascade-delete associated test cases."""
        dataset = await self.get_dataset(dataset_id)
        await self.repo.delete(dataset)

    async def add_cases(self, dataset_id: str, cases_data: list[TestCaseCreate]) -> list[TestCase]:
        """Append test cases to an existing dataset."""
        dataset = await self.get_dataset(dataset_id)

        # Check limit
        current_cases = len(dataset.test_cases)
        if current_cases + len(cases_data) > self.settings.MAX_CASES_PER_DATASET:
            raise PayloadTooLargeError(
                f"Adding {len(cases_data)} cases would exceed limit of {self.settings.MAX_CASES_PER_DATASET}",
                max_bytes=self.settings.MAX_CASES_PER_DATASET,
            )

        orm_cases = []
        for item in cases_data:
            tc = TestCase(
                dataset_id=dataset.id,
                prompt=item.prompt,
                expected_output=item.expected_output,
                context=item.context,
            )
            tc.tags = item.tags
            tc.metadata_dict = item.metadata
            tc.evaluator_config = item.evaluator_config
            orm_cases.append(tc)

        inserted = await self.repo.add_cases(dataset_id, orm_cases)
        dataset.version += 1
        await self.repo.flush()
        return inserted

    async def import_content(
        self,
        name: str,
        content: str,
        format_type: str,
        description: str | None = None,
    ) -> DatasetImportResponse:
        """Parse raw JSONL or CSV content, validate rows, and persist valid test cases."""
        if len(content.encode("utf-8")) > self.settings.MAX_DATASET_FILE_SIZE_BYTES:
            raise PayloadTooLargeError(
                f"Uploaded file exceeds {self.settings.MAX_DATASET_FILE_SIZE_BYTES} bytes limit",
                max_bytes=self.settings.MAX_DATASET_FILE_SIZE_BYTES,
            )

        format_clean = format_type.lower().strip()
        if format_clean in ("jsonl", "application/jsonl", "ndjson"):
            cases, errors = parse_jsonl_content(content)
        elif format_clean in ("csv", "text/csv", "tsv", "text/tab-separated-values"):
            cases, errors = parse_csv_content(content)
        else:
            raise DataValidationError(
                f"Unsupported import format: '{format_type}'. Use JSONL or CSV."
            )

        if not cases:
            raise DataValidationError(
                "No valid test cases found in uploaded content.",
                details={"errors": [e.model_dump() for e in errors]},
            )

        # Create dataset
        dataset = await self.create_dataset(
            DatasetCreate(
                name=name,
                description=description or f"Imported via {format_clean.upper()}",
                tags=["imported", format_clean],
                cases=cases,
            )
        )

        return DatasetImportResponse(
            dataset_id=dataset.id,
            name=dataset.name,
            imported_cases=len(cases),
            failed_rows=len(errors),
            errors=errors,
        )
