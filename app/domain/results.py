"""Case-result, metric-result, and aggregate scoring schemas."""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class MetricResult(BaseModel):
    """The outcome of a single evaluator applied to a case."""

    model_config = ConfigDict(frozen=True)

    metric_id: str = Field(..., description="Unique metric identifier")
    metric_name: str = Field(..., description="Display name for metric")
    score: float | None = Field(default=None, description="Normalized score typically [0.0, 1.0]")
    passed: bool | None = Field(default=None, description="Explicit pass/fail judgment")
    reason: str | None = Field(default=None, description="Explanatory feedback or rationale")
    details: dict[str, Any] = Field(default_factory=dict, description="Diagnostic payload")
    is_model_based: bool = Field(default=False, description="True if scored via LLM-as-judge")


class CaseResult(BaseModel):
    """The execution and evaluation result for a single test case."""

    model_config = ConfigDict(frozen=True)

    case_id: str = Field(..., description="Evaluation case identifier")
    run_id: str = Field(..., description="Parent evaluation run identifier")
    input: str | dict[str, Any] = Field(...)
    actual_output: str | dict[str, Any] | None = Field(default=None)
    expected_output: str | dict[str, Any] | None = Field(default=None)
    metrics: list[MetricResult] = Field(default_factory=list)
    latency_ms: float | None = Field(default=None, ge=0.0)
    token_usage: dict[str, int] | None = Field(default=None)
    error_category: str | None = Field(default=None)
    error_message: str | None = Field(default=None)
    trace: dict[str, Any] | None = Field(default=None)


class AggregateMetrics(BaseModel):
    """Dataset-level aggregated performance summary."""

    model_config = ConfigDict(frozen=True)

    total_cases: int = Field(default=0, ge=0)
    completed_cases: int = Field(default=0, ge=0)
    failed_cases: int = Field(default=0, ge=0)
    pass_rate: float | None = Field(default=None, ge=0.0, le=1.0)
    mean_latency_ms: float | None = Field(default=None, ge=0.0)
    median_latency_ms: float | None = Field(default=None, ge=0.0)
    p95_latency_ms: float | None = Field(default=None, ge=0.0)
    total_tokens: int | None = Field(default=None, ge=0)
    metric_averages: dict[str, float] = Field(default_factory=dict)
    metric_pass_rates: dict[str, float] = Field(default_factory=dict)
    category_performance: dict[str, dict[str, float]] = Field(default_factory=dict)
    error_distribution: dict[str, int] = Field(default_factory=dict)
