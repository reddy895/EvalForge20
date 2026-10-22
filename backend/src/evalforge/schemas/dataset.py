"""Pydantic v2 schemas for Dataset and TestCase entities."""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class TestCaseCreate(BaseModel):
    __test__ = False
    model_config = ConfigDict(from_attributes=True)

    prompt: str = Field(..., min_length=1, description="Input prompt or conversation to evaluate")
    expected_output: str | None = Field(None, description="Ground truth or reference target answer")
    context: str | None = Field(None, description="Retrieved context document or system background")
    tags: list[str] = Field(
        default_factory=list, description="Tags for categorization or filtering"
    )
    metadata: dict[str, Any] = Field(default_factory=dict, description="Arbitrary task metadata")
    evaluator_config: dict[str, Any] = Field(
        default_factory=dict, description="Custom metric configuration"
    )


class TestCaseUpdate(BaseModel):
    __test__ = False
    model_config = ConfigDict(from_attributes=True)

    prompt: str | None = None
    expected_output: str | None = None
    context: str | None = None
    tags: list[str] | None = None
    metadata: dict[str, Any] | None = None
    evaluator_config: dict[str, Any] | None = None


class TestCaseResponse(BaseModel):
    __test__ = False
    model_config = ConfigDict(from_attributes=True)

    id: str
    dataset_id: str
    prompt: str
    expected_output: str | None = None
    context: str | None = None
    tags: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    evaluator_config: dict[str, Any] = Field(default_factory=dict)
    created_at: str
    updated_at: str


class DatasetCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str = Field(..., min_length=1, max_length=255, description="Unique name of dataset")
    description: str | None = Field(None, description="Detailed description of dataset purpose")
    tags: list[str] = Field(default_factory=list, description="Categorization tags")
    cases: list[TestCaseCreate] | None = Field(None, description="Initial list of test cases")


class DatasetUpdate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    tags: list[str] | None = None


class DatasetResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    description: str | None = None
    version: int
    tags: list[str] = Field(default_factory=list)
    case_count: int = 0
    created_at: str
    updated_at: str


class DatasetDetailResponse(DatasetResponse):
    cases: list[TestCaseResponse] = Field(default_factory=list)


class DatasetListResponse(BaseModel):
    total: int
    items: list[DatasetResponse]


class RowImportError(BaseModel):
    line: int
    raw_data: str
    error: str


class DatasetImportResponse(BaseModel):
    dataset_id: str
    name: str
    imported_cases: int
    failed_rows: int
    errors: list[RowImportError] = Field(default_factory=list)
