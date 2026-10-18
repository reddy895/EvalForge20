"""Request and response schemas for FastAPI endpoints."""

from pydantic import BaseModel, Field

from app.domain.models import EvaluatorConfiguration, TargetConfiguration


class DatasetValidateRequest(BaseModel):
    """Payload to validate a dataset supplied directly as JSONL text."""

    content: str = Field(..., min_length=1, description="Raw JSONL dataset content")


class CreateEvaluationRequest(BaseModel):
    """Payload to launch a new evaluation run."""

    name: str = Field(default="Evaluation Run", min_length=1)
    dataset_path: str | None = Field(default=None, description="Path to local JSONL dataset file")
    dataset_content: str | None = Field(
        default=None, description="Raw JSONL dataset content if supplied directly"
    )
    target: TargetConfiguration
    evaluators: list[EvaluatorConfiguration] = Field(
        default_factory=lambda: [
            EvaluatorConfiguration(evaluator_name="Exact Match", metric_id="exact_match"),
            EvaluatorConfiguration(evaluator_name="Normalized Match", metric_id="normalized_match"),
        ]
    )
    max_concurrency: int = Field(default=5, ge=1, le=50)
    max_retries: int = Field(default=2, ge=0, le=5)
    timeout_seconds: float = Field(default=60.0, gt=0.0)


class RunSummaryResponse(BaseModel):
    """Summary of an evaluation run returned by API."""

    run_id: str
    name: str
    status: str
    total_cases: int
    completed_cases: int
    failed_cases: int
    started_at: str | None
    completed_at: str | None
    pass_rate: float | None
    error_message: str | None
    model_identifier: str | None = None
    provider_name: str | None = None
    mean_latency_ms: float | None = None
    total_tokens: int | None = None


class ProviderHealthReport(BaseModel):
    """Diagnostic health state for a single model provider."""

    provider_name: str
    status: str
    is_local: bool
    details: dict[str, str | int | bool | None] = Field(default_factory=dict)


class SystemReadinessResponse(BaseModel):
    """Detailed system and provider readiness report."""

    status: str
    database: str
    version: str
    environment: str
    available_providers: list[str]
    providers_status: dict[str, str] = Field(default_factory=dict)
    langsmith_enabled: bool
