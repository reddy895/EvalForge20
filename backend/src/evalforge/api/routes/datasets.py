"""Modular API route for dataset management, file uploads, and test-case creation."""

import uuid
from typing import Any
from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import PlainTextResponse

from src.evalforge.datasets.exporter import export_dataset_to_csv, export_dataset_to_jsonl
from src.evalforge.datasets.loader import DatasetLoader
from src.evalforge.datasets.validator import validate_dataset_records
from src.evalforge.services.dataset_service import get_dataset_service
from src.evalforge.storage.models.dataset import Dataset, TestCase

router = APIRouter(prefix="/datasets", tags=["datasets"])


@router.get("")
async def list_datasets() -> dict[str, Any]:
    service = get_dataset_service()
    datasets = await service.list_datasets()
    return {
        "total": len(datasets),
        "datasets": [
            {
                "id": str(d.id),
                "name": d.name,
                "description": d.description,
                "task_type": d.task_type,
                "version": d.version,
                "test_cases_count": len(d.test_cases),
                "created_at": d.created_at.isoformat() if d.created_at else None,
            }
            for d in datasets
        ],
    }


@router.post("")
async def create_dataset(
    name: str = Form(...),
    description: str | None = Form(None),
    task_type: str = Form("general"),
    file: UploadFile | None = File(None),
    raw_content: str | None = Form(None),
) -> dict[str, Any]:
    service = get_dataset_service()

    content = ""
    filename = "data.json"
    if file:
        content = (await file.read()).decode("utf-8")
        filename = file.filename or "data.json"
    elif raw_content:
        content = raw_content

    if not content.strip():
        raise HTTPException(status_code=400, detail="Either a file upload or raw_content must be provided.")

    parsed_records = DatasetLoader.load_from_text(content, filename_or_ext=filename)
    dict_records = [r.model_dump() for r in parsed_records]
    report = validate_dataset_records(dict_records)

    if not report.is_valid:
        raise HTTPException(status_code=422, detail=f"Dataset validation failed: {report.errors}")

    dataset = await service.create_dataset_with_cases(
        name=name,
        description=description,
        task_type=task_type,
        cases=dict_records,
    )

    return {
        "success": True,
        "dataset_id": str(dataset.id),
        "name": dataset.name,
        "cases_count": len(dataset.test_cases),
        "fingerprint": report.fingerprint,
    }


@router.get("/{dataset_id}")
async def get_dataset(dataset_id: str) -> dict[str, Any]:
    service = get_dataset_service()
    dataset = await service.get_dataset_by_id(dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail=f"Dataset '{dataset_id}' not found.")

    return {
        "id": str(dataset.id),
        "name": dataset.name,
        "description": dataset.description,
        "task_type": dataset.task_type,
        "version": dataset.version,
        "cases": [
            {
                "id": str(c.id),
                "input": c.prompt,
                "expected_output": c.expected_output,
                "context": c.context,
                "metadata": c.metadata_dict,
            }
            for c in dataset.test_cases
        ],
    }


@router.get("/{dataset_id}/export")
async def export_dataset(dataset_id: str, format: str = "jsonl") -> PlainTextResponse:
    service = get_dataset_service()
    dataset = await service.get_dataset_by_id(dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail=f"Dataset '{dataset_id}' not found.")

    if format.lower() == "csv":
        data = export_dataset_to_csv(dataset)
        media_type = "text/csv"
    else:
        data = export_dataset_to_jsonl(dataset)
        media_type = "application/x-ndjson"

    return PlainTextResponse(content=data, media_type=media_type)
