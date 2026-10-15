"""Dataset and dataset-version domain models."""

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.domain.models import EvaluationCase


class DatasetStats(BaseModel):
    """Aggregate statistics for a dataset version."""

    model_config = ConfigDict(frozen=True)

    total_cases: int = Field(default=0, ge=0)
    cases_with_expected_output: int = Field(default=0, ge=0)
    categories_distribution: dict[str, int] = Field(default_factory=dict)
    tags_distribution: dict[str, int] = Field(default_factory=dict)
    has_context_count: int = Field(default=0, ge=0)
    has_tools_count: int = Field(default=0, ge=0)


class DatasetVersion(BaseModel):
    """An immutable versioned snapshot of an evaluation dataset."""

    model_config = ConfigDict(frozen=True)

    version_id: str = Field(..., description="Unique version identifier")
    dataset_id: str = Field(..., description="Parent dataset identifier")
    version_number: int = Field(default=1, ge=1)
    content_hash: str = Field(..., description="SHA-256 hash of dataset cases")
    cases: list[EvaluationCase] = Field(default_factory=list)
    stats: DatasetStats = Field(default_factory=DatasetStats)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Dataset(BaseModel):
    """A logical dataset grouping multiple versions."""

    model_config = ConfigDict(frozen=True)

    id: str = Field(..., min_length=1, description="Unique slug or ID of dataset")
    name: str = Field(..., min_length=1, description="Human readable dataset name")
    description: str | None = Field(default=None)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    latest_version: int = Field(default=1, ge=1)
