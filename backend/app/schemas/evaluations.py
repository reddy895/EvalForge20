"""Schemas for evaluation datasets, test cases, execution, and persistent history."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class EvaluationCase(BaseModel):
    id: str
    prompt: str
    expected_output: str | None = None
    task_category: str = "general"
    assertions: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class CaseMetricResult(BaseModel):
    metric_name: str
    passed: bool
    score: float
    details: str | None = None


class CaseResult(BaseModel):
    case_id: str
    prompt: str
    expected_output: str | None = None
    actual_output: str | None = None
    passed: bool
    latency_ms: float
    error_message: str | None = None
    error_category: str | None = None
    metrics: list[CaseMetricResult] = Field(default_factory=list)


class AggregateMetrics(BaseModel):
    total_cases: int
    completed_cases: int
    failed_cases: int
    pass_rate: float | None = None
    mean_latency_ms: float | None = None
    p95_latency_ms: float | None = None
    total_tokens: int | None = None
    metric_averages: dict[str, float] = Field(default_factory=dict)
    error_distribution: dict[str, int] = Field(default_factory=dict)


class EvaluationRunCreate(BaseModel):
    name: str = Field(..., description="Human-readable name for evaluation run")
    model_identifier: str = Field(
        ..., description="Target model identifier, e.g. 'qwen2.5:3b' or 'mock-model-v1'"
    )
    provider: str = Field(
        default="ollama", description="Provider adapter to route to: 'ollama' or 'mock'"
    )
    task_id: str = Field(
        default="coding_basics", description="Benchmark task ID to evaluate against"
    )
    max_cases: int = Field(default=5, ge=1, le=100)
    temperature: float = Field(default=0.0, ge=0.0, le=2.0)


class EvaluationRunSummary(BaseModel):
    id: str
    name: str
    model_identifier: str
    provider: str
    task_id: str
    status: str
    total_cases: int
    completed_cases: int
    pass_rate: float | None = None
    mean_latency_ms: float | None = None
    created_at: datetime
    completed_at: datetime | None = None


class EvaluationRunDetail(BaseModel):
    id: str
    name: str
    model_identifier: str
    provider: str
    task_id: str
    status: str
    total_cases: int
    completed_cases: int
    pass_rate: float | None = None
    aggregates: AggregateMetrics
    case_results: list[CaseResult]
    created_at: datetime
    completed_at: datetime | None = None
