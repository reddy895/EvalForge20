"""API endpoints for Dataset and TestCase management."""

from fastapi import APIRouter, Depends, File, Form, Query, Response, UploadFile, status
from fastapi.responses import PlainTextResponse
from sqlalchemy.ext.asyncio import AsyncSession

from src.evalforge.core.errors import DataValidationError, NotFoundError
from src.evalforge.core.security import sanitize_filename
from src.evalforge.datasets.exporter import export_dataset_to_csv, export_dataset_to_jsonl
from src.evalforge.schemas.dataset import (
    DatasetCaseListResponse,
    DatasetCreate,
    DatasetDetailResponse,
    DatasetImportResponse,
    DatasetIntegrityResponse,
    DatasetListResponse,
    DatasetPreviewResponse,
    DatasetResponse,
    DatasetUpdate,
    TestCaseCreate,
    TestCaseResponse,
)
from src.evalforge.services.dataset_service import DatasetService
from src.evalforge.storage.database import get_db

datasets_router = APIRouter(prefix="/datasets", tags=["Datasets"])


@datasets_router.post(
    "",
    response_model=DatasetDetailResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new dataset",
)
async def create_dataset(
    payload: DatasetCreate,
    db: AsyncSession = Depends(get_db),
) -> DatasetDetailResponse:
    """Create a new dataset with optional initial test cases."""
    service = DatasetService(db)
    dataset = await service.create_dataset(payload)
    # Refresh to load test cases
    dataset_with_cases = await service.get_dataset_with_cases(dataset.id)

    cases_resp = [
        TestCaseResponse(
            id=c.id,
            dataset_id=c.dataset_id,
            prompt=c.prompt,
            expected_output=c.expected_output,
            context=c.context,
            tags=c.tags,
            metadata=c.metadata_dict,
            evaluator_config=c.evaluator_config,
            created_at=c.created_at.isoformat(),
            updated_at=c.updated_at.isoformat(),
        )
        for c in dataset_with_cases.test_cases
    ]

    return DatasetDetailResponse(
        id=dataset.id,
        name=dataset.name,
        description=dataset.description,
        version=dataset.version,
        tags=dataset.tags,
        case_count=len(cases_resp),
        created_at=dataset.created_at.isoformat(),
        updated_at=dataset.updated_at.isoformat(),
        cases=cases_resp,
    )


@datasets_router.get("", response_model=DatasetListResponse, summary="List datasets")
async def list_datasets(
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> DatasetListResponse:
    """List paginated datasets with their case count."""
    service = DatasetService(db)
    total, items = await service.list_datasets(offset=offset, limit=limit)

    return DatasetListResponse(
        total=total,
        items=[
            DatasetResponse(
                id=d.id,
                name=d.name,
                description=d.description,
                version=d.version,
                tags=d.tags,
                case_count=count,
                created_at=d.created_at.isoformat(),
                updated_at=d.updated_at.isoformat(),
            )
            for d, count in items
        ],
    )


@datasets_router.post(
    "/import",
    response_model=DatasetImportResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Import dataset from JSONL or CSV file",
)
async def import_dataset(
    name: str = Form(..., description="Dataset name to create"),
    format: str = Form("jsonl", description="Format: 'jsonl' or 'csv'"),
    description: str | None = Form(None, description="Optional description"),
    file: UploadFile = File(..., description="Uploaded dataset file"),
    db: AsyncSession = Depends(get_db),
) -> DatasetImportResponse:
    """Import test cases from an uploaded JSONL or CSV file with validation."""
    service = DatasetService(db)
    max_bytes = service.settings.MAX_DATASET_FILE_SIZE_BYTES
    content_bytes = await file.read(max_bytes + 1)
    if len(content_bytes) > max_bytes:
        from src.evalforge.core.errors import PayloadTooLargeError

        raise PayloadTooLargeError(
            f"Uploaded file exceeds the {max_bytes} byte limit.",
            max_bytes=max_bytes,
        )
    if not content_bytes:
        raise DataValidationError("Uploaded file is empty.")
    try:
        content_str = content_bytes.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise DataValidationError(
            "Uploaded file is not valid UTF-8. Re-encode the file as UTF-8 before importing.",
            details={"byte_offset": exc.start},
        ) from exc

    return await service.import_content(
        name=name,
        content=content_str,
        format_type=format,
        description=description,
    )


@datasets_router.get(
    "/{dataset_id}/export",
    summary="Export dataset to JSONL or CSV",
    response_class=PlainTextResponse,
)
async def export_dataset(
    dataset_id: str,
    format: str = Query("jsonl", pattern="^(jsonl|csv)$"),
    db: AsyncSession = Depends(get_db),
) -> Response:
    """Export all test cases in the dataset as a downloadable JSONL or CSV file."""
    service = DatasetService(db)
    dataset = await service.get_dataset_with_cases(dataset_id)
    if format == "csv":
        csv_text = export_dataset_to_csv(dataset)
        filename = sanitize_filename(f"{dataset.name.lower().replace(' ', '_')}_export.csv")
        return Response(
            content=csv_text,
            media_type="text/csv",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )

    jsonl_text = export_dataset_to_jsonl(dataset)
    filename = sanitize_filename(f"{dataset.name.lower().replace(' ', '_')}_export.jsonl")
    return Response(
        content=jsonl_text,
        media_type="application/x-ndjson",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@datasets_router.get(
    "/{dataset_id}/cases",
    response_model=DatasetCaseListResponse,
    summary="List dataset test cases with pagination",
)
async def list_dataset_cases(
    dataset_id: str,
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
) -> DatasetCaseListResponse:
    """Return a bounded page of test cases without loading the entire dataset."""
    service = DatasetService(db)
    total, cases = await service.list_cases(dataset_id, offset=offset, limit=limit)
    return DatasetCaseListResponse(
        total=total,
        offset=offset,
        limit=limit,
        items=[
            TestCaseResponse(
                id=c.id,
                dataset_id=c.dataset_id,
                prompt=c.prompt,
                expected_output=c.expected_output,
                context=c.context,
                tags=c.tags,
                metadata=c.metadata_dict,
                evaluator_config=c.evaluator_config,
                created_at=c.created_at.isoformat(),
                updated_at=c.updated_at.isoformat(),
            )
            for c in cases
        ],
    )


@datasets_router.get(
    "/{dataset_id}/preview",
    response_model=DatasetPreviewResponse,
    summary="Preview the first test cases in a dataset",
)
async def preview_dataset(
    dataset_id: str,
    limit: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> DatasetPreviewResponse:
    """Return dataset metadata plus a small preview of cases for import verification."""
    service = DatasetService(db)
    dataset = await service.get_dataset(dataset_id)
    total, cases = await service.list_cases(dataset_id, offset=0, limit=limit)
    return DatasetPreviewResponse(
        dataset_id=dataset.id,
        name=dataset.name,
        version=dataset.version,
        total_cases=total,
        items=[
            TestCaseResponse(
                id=c.id,
                dataset_id=c.dataset_id,
                prompt=c.prompt,
                expected_output=c.expected_output,
                context=c.context,
                tags=c.tags,
                metadata=c.metadata_dict,
                evaluator_config=c.evaluator_config,
                created_at=c.created_at.isoformat(),
                updated_at=c.updated_at.isoformat(),
            )
            for c in cases
        ],
    )


@datasets_router.get(
    "/{dataset_id}/integrity",
    response_model=DatasetIntegrityResponse,
    summary="Validate dataset content and compute its fingerprint",
)
async def check_dataset_integrity(
    dataset_id: str,
    db: AsyncSession = Depends(get_db),
) -> DatasetIntegrityResponse:
    """Report empty prompts, duplicates, and a stable content fingerprint."""
    service = DatasetService(db)
    report = await service.check_integrity(dataset_id)
    return DatasetIntegrityResponse(**report)


@datasets_router.post(
    "/{dataset_id}/duplicate",
    response_model=DatasetResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Duplicate a dataset with all test cases",
)
async def duplicate_dataset(
    dataset_id: str,
    new_name: str | None = Query(None, max_length=255),
    db: AsyncSession = Depends(get_db),
) -> DatasetResponse:
    """Create an independent deep copy so edits never mutate the source."""
    service = DatasetService(db)
    clone = await service.duplicate_dataset(dataset_id, new_name=new_name)
    return DatasetResponse(
        id=clone.id,
        name=clone.name,
        description=clone.description,
        version=clone.version,
        tags=clone.tags,
        case_count=0,
        created_at=clone.created_at.isoformat(),
        updated_at=clone.updated_at.isoformat(),
    )


@datasets_router.delete(
    "/{dataset_id}/cases/{case_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an individual test case",
)
async def delete_test_case(
    dataset_id: str,
    case_id: str,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Remove a single case, verifying it belongs to the named dataset."""
    service = DatasetService(db)
    dataset = await service.get_dataset(dataset_id)
    case = await service.repo.get_case(case_id)
    if case is None or case.dataset_id != dataset.id:
        raise NotFoundError("TestCase", case_id)
    await service.repo.delete_case(case_id)


@datasets_router.get(
    "/{dataset_id}",
    response_model=DatasetDetailResponse,
    summary="Get dataset details",
)
async def get_dataset(
    dataset_id: str,
    db: AsyncSession = Depends(get_db),
) -> DatasetDetailResponse:
    """Fetch complete dataset details and all its test cases."""
    service = DatasetService(db)
    dataset = await service.get_dataset_with_cases(dataset_id)

    cases_resp = [
        TestCaseResponse(
            id=c.id,
            dataset_id=c.dataset_id,
            prompt=c.prompt,
            expected_output=c.expected_output,
            context=c.context,
            tags=c.tags,
            metadata=c.metadata_dict,
            evaluator_config=c.evaluator_config,
            created_at=c.created_at.isoformat(),
            updated_at=c.updated_at.isoformat(),
        )
        for c in dataset.test_cases
    ]

    return DatasetDetailResponse(
        id=dataset.id,
        name=dataset.name,
        description=dataset.description,
        version=dataset.version,
        tags=dataset.tags,
        case_count=len(cases_resp),
        created_at=dataset.created_at.isoformat(),
        updated_at=dataset.updated_at.isoformat(),
        cases=cases_resp,
    )


@datasets_router.patch(
    "/{dataset_id}",
    response_model=DatasetResponse,
    summary="Update dataset metadata",
)
async def update_dataset(
    dataset_id: str,
    payload: DatasetUpdate,
    db: AsyncSession = Depends(get_db),
) -> DatasetResponse:
    """Update dataset name, description, or tags."""
    service = DatasetService(db)
    dataset = await service.update_dataset(dataset_id, payload)
    return DatasetResponse(
        id=dataset.id,
        name=dataset.name,
        description=dataset.description,
        version=dataset.version,
        tags=dataset.tags,
        case_count=len(dataset.test_cases),
        created_at=dataset.created_at.isoformat(),
        updated_at=dataset.updated_at.isoformat(),
    )


@datasets_router.delete(
    "/{dataset_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete dataset",
)
async def delete_dataset(
    dataset_id: str,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete dataset and all nested test cases."""
    service = DatasetService(db)
    await service.delete_dataset(dataset_id)


@datasets_router.post(
    "/{dataset_id}/cases",
    response_model=list[TestCaseResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Add test cases to dataset",
)
async def add_test_cases(
    dataset_id: str,
    payload: list[TestCaseCreate],
    db: AsyncSession = Depends(get_db),
) -> list[TestCaseResponse]:
    """Append one or more test cases to an existing dataset."""
    service = DatasetService(db)
    new_cases = await service.add_cases(dataset_id, payload)
    return [
        TestCaseResponse(
            id=c.id,
            dataset_id=c.dataset_id,
            prompt=c.prompt,
            expected_output=c.expected_output,
            context=c.context,
            tags=c.tags,
            metadata=c.metadata_dict,
            evaluator_config=c.evaluator_config,
            created_at=c.created_at.isoformat(),
            updated_at=c.updated_at.isoformat(),
        )
        for c in new_cases
    ]
