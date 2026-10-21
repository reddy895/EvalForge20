"""Pydantic v2 schemas for Dataset and TestCase entities."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class TestCaseCreate(BaseModel):
    __test__ = False
    model_config = ConfigDict(from_attributes=True)

    prompt: str = Field(..., min_length=1, description="Input prompt or conversation to evaluate")
    expected_output: Optional[str] = Field(None, description="Ground truth or reference target answer")
    context: Optional[str] = Field(None, description="Retrieved context document or system background")
    tags: List[str] = Field(default_factory=list, description="Tags for categorization or filtering")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Arbitrary task metadata")
    evaluator_config: Dict[str, Any] = Field(default_factory=dict, description="Custom metric configuration")


class TestCaseUpdate(BaseModel):
    __test__ = False
    model_config = ConfigDict(from_attributes=True)

    prompt: Optional[str] = None
    expected_output: Optional[str] = None
    context: Optional[str] = None
    tags: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None
    evaluator_config: Optional[Dict[str, Any]] = None


class TestCaseResponse(BaseModel):
    __test__ = False
    model_config = ConfigDict(from_attributes=True)

    id: str
    dataset_id: str
    prompt: str
    expected_output: Optional[str] = None
    context: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    evaluator_config: Dict[str, Any] = Field(default_factory=dict)
    created_at: str
    updated_at: str


class DatasetCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str = Field(..., min_length=1, max_length=255, description="Unique name of dataset")
    description: Optional[str] = Field(None, description="Detailed description of dataset purpose")
    tags: List[str] = Field(default_factory=list, description="Categorization tags")
    cases: Optional[List[TestCaseCreate]] = Field(None, description="Initial list of test cases")


class DatasetUpdate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    tags: Optional[List[str]] = None


class DatasetResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    description: Optional[str] = None
    version: int
    tags: List[str] = Field(default_factory=list)
    case_count: int = 0
    created_at: str
    updated_at: str


class DatasetDetailResponse(DatasetResponse):
    cases: List[TestCaseResponse] = Field(default_factory=list)


class DatasetListResponse(BaseModel):
    total: int
    items: List[DatasetResponse]


class RowImportError(BaseModel):
    line: int
    raw_data: str
    error: str


class DatasetImportResponse(BaseModel):
    dataset_id: str
    name: str
    imported_cases: int
    failed_rows: int
    errors: List[RowImportError] = Field(default_factory=list)
