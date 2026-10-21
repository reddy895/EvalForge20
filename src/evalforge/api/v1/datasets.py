"""API endpoints for Dataset and TestCase management."""

from typing import List, Optional
from fastapi import APIRouter, Depends, File, Form, Query, Response, UploadFile, status
from fastapi.responses import PlainTextResponse
from sqlalchemy.ext.asyncio import AsyncSession

from src.evalforge.datasets.exporter import export_dataset_to_jsonl
from src.evalforge.schemas.dataset import (
    DatasetCreate,
    DatasetDetailResponse,
    DatasetImportResponse,
    DatasetListResponse,
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
    description: Optional[str] = Form(None, description="Optional description"),
    file: UploadFile = File(..., description="Uploaded dataset file"),
    db: AsyncSession = Depends(get_db),
) -> DatasetImportResponse:
    """Import test cases from an uploaded JSONL or CSV file with validation."""
    content_bytes = await file.read()
    content_str = content_bytes.decode("utf-8", errors="replace")

    service = DatasetService(db)
    return await service.import_content(
        name=name,
        content=content_str,
        format_type=format,
        description=description,
    )


@datasets_router.get(
    "/{dataset_id}/export",
    summary="Export dataset to JSONL",
    response_class=PlainTextResponse,
)
async def export_dataset(
    dataset_id: str,
    db: AsyncSession = Depends(get_db),
) -> Response:
    """Export all test cases in the dataset as a downloadable JSONL file."""
    service = DatasetService(db)
    dataset = await service.get_dataset_with_cases(dataset_id)
    jsonl_text = export_dataset_to_jsonl(dataset)

    filename = f"{dataset.name.lower().replace(' ', '_')}_export.jsonl"
    return Response(
        content=jsonl_text,
        media_type="application/x-ndjson",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


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
    response_model=List[TestCaseResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Add test cases to dataset",
)
async def add_test_cases(
    dataset_id: str,
    payload: List[TestCaseCreate],
    db: AsyncSession = Depends(get_db),
) -> List[TestCaseResponse]:
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
