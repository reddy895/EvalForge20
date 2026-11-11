"""Dataset application service managing datasets, test cases, and imports."""

from sqlalchemy.ext.asyncio import AsyncSession

from src.evalforge.core.config import get_settings
from src.evalforge.core.errors import (
    DataValidationError,
    EntityConflictError,
    NotFoundError,
    PayloadTooLargeError,
)
from src.evalforge.datasets.fingerprint import compute_dataset_fingerprint
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
        self,
        offset: int = 0,
        limit: int = 50,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> tuple[int, list[tuple[Dataset, int]]]:
        """Return total count and paginated datasets with their case count."""
        total = await self.repo.count()
        items = await self.repo.list_with_counts(
            offset=offset,
            limit=limit,
            sort_by=sort_by,
            sort_order=sort_order,
        )
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

    async def list_cases(
        self, dataset_id: str, offset: int = 0, limit: int = 100
    ) -> tuple[int, list[TestCase]]:
        """Return a paginated page of cases without loading the whole dataset."""
        await self.get_dataset(dataset_id)
        return await self.repo.list_cases(dataset_id, offset=offset, limit=limit)

    async def duplicate_dataset(self, dataset_id: str, new_name: str | None = None) -> Dataset:
        """Deep-copy a dataset and all of its test cases under a new name."""
        source = await self.get_dataset_with_cases(dataset_id)
        target_name = (new_name or f"{source.name} (copy)").strip()
        existing = await self.repo.get_by_name(target_name)
        if existing:
            raise EntityConflictError(f"A dataset with name '{target_name}' already exists.")
        if len(source.test_cases) > self.settings.MAX_CASES_PER_DATASET:
            raise PayloadTooLargeError(
                "Source dataset exceeds the maximum case limit for duplication.",
                max_bytes=self.settings.MAX_CASES_PER_DATASET,
            )

        clone = Dataset(
            name=target_name,
            description=source.description,
            version=source.version,
        )
        clone.tags = list(source.tags)
        await self.repo.add(clone)

        orm_cases = []
        for case in source.test_cases:
            tc = TestCase(
                dataset_id=clone.id,
                prompt=case.prompt,
                expected_output=case.expected_output,
                context=case.context,
            )
            tc.tags = list(case.tags)
            tc.metadata_dict = dict(case.metadata_dict)
            tc.evaluator_config = dict(case.evaluator_config)
            orm_cases.append(tc)
        if orm_cases:
            await self.repo.add_cases(clone.id, orm_cases)
        return clone

    async def check_integrity(self, dataset_id: str) -> dict[str, object]:
        """Compute a content fingerprint and surface data-quality issues."""
        dataset = await self.get_dataset_with_cases(dataset_id)
        records = [
            {
                "id": case.id,
                "prompt": case.prompt,
                "expected_output": case.expected_output,
            }
            for case in dataset.test_cases
        ]
        fingerprint = compute_dataset_fingerprint(records)

        empty_prompts = 0
        seen: dict[tuple[str, str], int] = {}
        issues: list[str] = []
        for case in dataset.test_cases:
            prompt = (case.prompt or "").strip()
            if not prompt:
                empty_prompts += 1
                issues.append(f"Case {case.id}: empty prompt.")
            key = (prompt, (case.expected_output or "").strip())
            seen[key] = seen.get(key, 0) + 1
            if not (case.expected_output or "").strip():
                issues.append(f"Case {case.id}: missing expected_output (only subjective metrics apply).")

        duplicate_prompts = sum(count - 1 for count in seen.values() if count > 1)
        if duplicate_prompts:
            issues.append(f"{duplicate_prompts} duplicate prompt/expected-output pair(s) detected.")
        if not dataset.test_cases:
            issues.append("Dataset contains no test cases.")

        return {
            "dataset_id": dataset.id,
            "name": dataset.name,
            "version": dataset.version,
            "case_count": len(dataset.test_cases),
            "fingerprint": fingerprint,
            "is_valid": empty_prompts == 0 and bool(dataset.test_cases),
            "empty_prompts": empty_prompts,
            "duplicate_prompts": duplicate_prompts,
            "issues": issues[:50],
        }

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

        # Deduplicate identical prompt/reference/context triples while retaining
        # every rejected row in the error report (nothing is silently discarded).
        unique_cases: list[TestCaseCreate] = []
        seen_keys: set[tuple[str, str, str]] = set()
        duplicates_skipped = 0
        warnings: list[str] = []
        for idx, case in enumerate(cases, start=1):
            key = (
                case.prompt.strip(),
                (case.expected_output or "").strip(),
                (case.context or "").strip(),
            )
            if key in seen_keys:
                duplicates_skipped += 1
                warnings.append(f"Row {idx}: duplicate prompt/reference/context triple skipped.")
                continue
            seen_keys.add(key)
            unique_cases.append(case)
        cases = unique_cases

        if len(cases) > self.settings.MAX_CASES_PER_DATASET:
            raise PayloadTooLargeError(
                f"Dataset has {len(cases)} unique cases, exceeding the maximum of "
                f"{self.settings.MAX_CASES_PER_DATASET}.",
                max_bytes=self.settings.MAX_CASES_PER_DATASET,
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
            duplicates_skipped=duplicates_skipped,
            warnings=warnings[:50],
            errors=errors,
        )


def get_dataset_service(session: AsyncSession | None = None) -> DatasetService:
    """Helper factory providing DatasetService with session context."""
    if session is None:
        from src.evalforge.storage.session import async_session_factory
        session = async_session_factory()
    return DatasetService(session)

