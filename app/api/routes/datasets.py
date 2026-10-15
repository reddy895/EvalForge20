"""Dataset validation and management API routes."""

from fastapi import APIRouter, status
from app.api.schemas import DatasetValidateRequest
from app.datasets.validator import DatasetValidationReport, validate_dataset

dataset_router = APIRouter(prefix="/v1/datasets", tags=["Datasets"])


@dataset_router.post(
    "/validate",
    response_model=DatasetValidationReport,
    status_code=status.HTTP_200_OK,
    summary="Validate raw JSONL dataset syntax and schema",
)
async def validate_dataset_endpoint(req: DatasetValidateRequest) -> DatasetValidationReport:
    """Validate JSONL string against evaluation case schema and check for duplicate IDs."""
    return validate_dataset(req.content)
