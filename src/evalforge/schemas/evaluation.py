"""Pydantic v2 schemas for Evaluation configurations, requests, and results."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class EvaluationConfig(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    metrics: List[str] = Field(
        default_factory=lambda: ["exact_match", "token_f1"],
        description="List of metric identifiers to compute for every test case",
    )
    concurrency: int = Field(default=4, ge=1, le=16, description="Parallel worker limit")
    temperature: float = Field(default=0.0, ge=0.0, le=2.0)
    top_p: Optional[float] = None
    seed: Optional[int] = None
    max_tokens: Optional[int] = None
    context_length: Optional[int] = None
    stop: Optional[List[str]] = None
    judge_model: Optional[str] = None
    rubric: Optional[str] = None


class EvaluationCreateRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: Optional[str] = Field(None, description="Optional custom name for this evaluation run")
    model_id: str = Field(..., description="Target model identifier (e.g. 'llama3.2' or 'mock-llama-3.1-8b')")
    provider: str = Field(default="ollama", description="Inference provider name ('ollama' or 'mock')")
    dataset_id: str = Field(..., description="ID of the dataset to evaluate")
    config: Optional[EvaluationConfig] = Field(default_factory=EvaluationConfig)


class CaseResultResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    case_id: str
    prompt: str
    expected_output: Optional[str] = None
    actual_output: Optional[str] = None
    passed: bool
    latency_ms: float
    metrics: Dict[str, Any] = Field(default_factory=dict)
    token_usage: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    created_at: str


class EvaluationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    model_id: str
    provider: str
    dataset_id: Optional[str] = None
    dataset_name: Optional[str] = None
    status: str
    total_cases: int
    completed_cases: int
    passed_cases: int
    failed_cases: int
    pass_rate: Optional[float] = None
    avg_latency_ms: Optional[float] = None
    summary_metrics: Dict[str, Any] = Field(default_factory=dict)
    error_message: Optional[str] = None
    created_at: str
    completed_at: Optional[str] = None


class EvaluationDetailResponse(EvaluationResponse):
    results: List[CaseResultResponse] = Field(default_factory=list)


class EvaluationListResponse(BaseModel):
    total: int
    items: List[EvaluationResponse]
