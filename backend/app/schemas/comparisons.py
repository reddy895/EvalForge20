"""Schemas for side-by-side model comparisons."""

from pydantic import BaseModel, Field


class ModelComparisonRequest(BaseModel):
    model_ids: list[str] = Field(
        ..., min_length=2, max_length=4, description="List of 2 to 4 model IDs to compare"
    )


class ComparisonRow(BaseModel):
    metric_name: str
    category: str
    values: dict[str, str | float | int | bool | None] = Field(
        ..., description="Mapping of model_id to value"
    )
    winner_model_id: str | None = None
    note: str | None = None


class ModelComparisonResult(BaseModel):
    compared_models: list[dict[str, str]]
    matrix: list[ComparisonRow]
    summary_verdict: str
    comparability_notes: list[str] = Field(default_factory=list)
