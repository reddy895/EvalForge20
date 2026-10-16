"""Dataset validation and management API routes."""

from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.api.schemas import DatasetValidateRequest
from app.config import get_settings
from app.datasets.loader import DatasetLoader
from app.datasets.validator import DatasetValidationReport, validate_dataset
from app.security import validate_safe_path

dataset_router = APIRouter(prefix="/v1/datasets", tags=["Datasets"])


class ImportDatasetRequest(BaseModel):
    """Payload to import and persist a new dataset file."""

    filename: str = Field(
        ..., min_length=1, description="Dataset filename (e.g. custom_eval.jsonl)"
    )
    content: str = Field(..., min_length=1, description="Raw dataset content")


@dataset_router.post(
    "/validate",
    response_model=DatasetValidationReport,
    status_code=status.HTTP_200_OK,
    summary="Validate raw JSONL dataset syntax and schema",
)
async def validate_dataset_endpoint(req: DatasetValidateRequest) -> DatasetValidationReport:
    """Validate JSONL string against evaluation case schema and check for duplicate IDs."""
    return validate_dataset(req.content)


@dataset_router.get(
    "",
    summary="List available dataset files in repository and data directory",
)
async def list_datasets_endpoint() -> list[dict[str, Any]]:
    """Scan and return discovered datasets with format, size, and case counts."""
    settings = get_settings()
    search_dirs = [Path("examples/datasets"), settings.data_dir]
    supported_extensions = {".jsonl", ".ndjson", ".json", ".csv"}

    results: list[dict[str, Any]] = []
    seen_paths: set[str] = set()

    for directory in search_dirs:
        if not directory.exists() or not directory.is_dir():
            continue

        for file_path in sorted(directory.iterdir()):
            if file_path.is_file() and file_path.suffix.lower() in supported_extensions:
                rel_path = str(file_path)
                if rel_path in seen_paths:
                    continue
                seen_paths.add(rel_path)

                try:
                    fmt = DatasetLoader.detect_format(file_path)
                    report = DatasetLoader.load(file_path)
                    case_count = report.valid_cases_count
                except Exception:
                    fmt = file_path.suffix.lstrip(".").lower()
                    case_count = 0

                results.append(
                    {
                        "name": file_path.name,
                        "path": rel_path,
                        "format": fmt.upper(),
                        "size_bytes": file_path.stat().st_size,
                        "case_count": case_count,
                    }
                )

    return results


@dataset_router.get(
    "/preview",
    summary="Preview parsed test cases and metadata for a dataset path",
)
async def preview_dataset_endpoint(
    path: str = Query(..., description="Path to dataset file"),
    limit: int = Query(default=50, ge=1, le=200),
) -> dict[str, Any]:
    """Return validated test cases and validation report for dataset inspector."""
    try:
        safe_path = validate_safe_path(path, must_exist=True)
        report = DatasetLoader.load(safe_path)
        cases_sample = [c.model_dump() for c in report.cases[:limit]]

        return {
            "path": str(safe_path),
            "filename": safe_path.name,
            "format": DatasetLoader.detect_format(safe_path).upper(),
            "is_valid": report.is_valid,
            "total_lines_read": report.total_lines_read,
            "valid_cases_count": report.valid_cases_count,
            "dataset_hash": report.dataset_hash,
            "issues": [i.model_dump() for i in report.issues],
            "cases": cases_sample,
        }
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unable to preview dataset at '{path}': {exc}",
        ) from exc


@dataset_router.post(
    "/import",
    status_code=status.HTTP_201_CREATED,
    summary="Import and persist a new dataset file",
)
async def import_dataset_endpoint(req: ImportDatasetRequest) -> dict[str, Any]:
    """Validate content and persist new dataset file inside project data directory."""
    settings = get_settings()
    clean_name = Path(req.filename).name
    if not clean_name.endswith((".jsonl", ".json", ".csv")):
        clean_name += ".jsonl"

    dest_path = settings.data_dir / clean_name
    safe_dest = validate_safe_path(dest_path)

    # Validate content first
    fmt = DatasetLoader.detect_format(safe_dest)
    report = DatasetLoader.validate_content(req.content, format=fmt)
    if not report.is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Dataset validation failed: {report.format_errors()}",
        )

    safe_dest.parent.mkdir(parents=True, exist_ok=True)
    safe_dest.write_text(req.content, encoding="utf-8")

    return {
        "message": f"Dataset '{clean_name}' successfully imported",
        "path": str(safe_dest),
        "filename": clean_name,
        "format": fmt.upper(),
        "valid_cases_count": report.valid_cases_count,
        "dataset_hash": report.dataset_hash,
    }
