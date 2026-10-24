"""Pydantic v2 schemas for Evaluation configurations, requests, and results."""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class EvaluationConfig(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    metrics: list[str] = Field(
        default_factory=lambda: ["exact_match", "token_f1"],
        description="List of metric identifiers to compute for every test case",
    )
    concurrency: int = Field(default=4, ge=1, le=16, description="Parallel worker limit")
    temperature: float = Field(default=0.0, ge=0.0, le=2.0)
    top_p: float | None = Field(default=None, ge=0.0, le=1.0)
    seed: int | None = None
    max_tokens: int | None = Field(default=None, ge=1, le=131072)
    context_length: int | None = Field(default=None, ge=128, le=1048576)
    stop: list[str] | None = None
    judge_model: str | None = None
    rubric: str | None = None
    timeout_seconds: float = Field(default=120.0, ge=1.0, le=600.0, description="Per-case timeout limit in seconds")


class EvaluationCreateRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str | None = Field(None, max_length=120, description="Optional custom name for this evaluation run")
    model_id: str = Field(
        ..., min_length=1, max_length=150, description="Target model identifier (e.g. 'llama3.2' or 'mock-llama-3.1-8b')"
    )
    provider: str = Field(
        default="ollama", min_length=1, max_length=64, description="Inference provider name ('ollama' or 'mock')"
    )
    dataset_id: str = Field(..., min_length=1, max_length=100, description="ID or slug of the dataset to evaluate")
    max_cases: int | None = Field(None, ge=1, le=10000, description="Optional cap on test cases to evaluate")
    config: EvaluationConfig | None = Field(default_factory=EvaluationConfig)

    @field_validator("model_id", "dataset_id", "provider")
    @classmethod
    def sanitize_identifiers(cls, val: str) -> str:
        s = val.strip()
        if not s:
            raise ValueError("Field cannot be empty or solely whitespace.")
        return s


class CaseResultResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    case_id: str
    prompt: str
    expected_output: str | None = None
    actual_output: str | None = None
    passed: bool
    latency_ms: float | None = None
    assertion_type: str | None = None
    tokens_per_second: float | None = None
    load_duration_ms: float | None = None
    metrics: dict[str, Any] = Field(default_factory=dict)
    token_usage: dict[str, Any] | None = None
    error_message: str | None = None
    created_at: str


class EvaluationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    model_id: str
    provider: str
    dataset_id: str | None = None
    dataset_name: str | None = None
    status: str
    total_cases: int
    completed_cases: int
    passed_cases: int
    failed_cases: int
    pass_rate: float | None = None
    error_rate: float | None = None
    avg_latency_ms: float | None = None
    median_latency_ms: float | None = None
    p95_latency_ms: float | None = None
    tokens_per_second: float | None = None
    load_duration_ms: float | None = None
    summary_metrics: dict[str, Any] = Field(default_factory=dict)
    error_message: str | None = None
    created_at: str
    completed_at: str | None = None


class EvaluationDetailResponse(EvaluationResponse):
    results: list[CaseResultResponse] = Field(default_factory=list)
    case_results: list[CaseResultResponse] = Field(default_factory=list)


class EvaluationListResponse(BaseModel):
    total: int
    items: list[EvaluationResponse]
