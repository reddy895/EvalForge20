"""Configuration models for evaluation runs."""

import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.config import get_settings
from app.domain.models import EvaluationCase, EvaluatorConfiguration, TargetConfiguration
from app.domain.results import AggregateMetrics
from app.domain.state import EvaluationRunStatus


class EvaluationRunConfig(BaseModel):
    """Specification defining the parameters of an evaluation run."""

    model_config = ConfigDict(frozen=True)

    run_id: str = Field(default_factory=lambda: f"run_{uuid.uuid4().hex[:12]}")
    name: str = Field(default="Evaluation Run")
    dataset_path: Path | str | None = Field(default=None)
    dataset_cases: list[EvaluationCase] | None = Field(default=None)
    dataset_version_hash: str | None = Field(default=None)
    target: TargetConfiguration
    evaluators: list[EvaluatorConfiguration] = Field(default_factory=list)
    max_concurrency: int = Field(
        default_factory=lambda: get_settings().max_concurrency, ge=1, le=50
    )
    max_retries: int = Field(default=2, ge=0, le=5)
    timeout_seconds: float = Field(
        default_factory=lambda: get_settings().default_timeout_seconds, gt=0.0
    )

    @property
    def model_identifier(self) -> str:
        return self.target.model_identifier

    @property
    def provider(self) -> str:
        return self.target.provider_name

    @property
    def dataset_name(self) -> str:
        if self.dataset_path:
            return Path(self.dataset_path).name
        return "in_memory_dataset"

    @property
    def options(self) -> dict[str, Any]:
        return self.target.extra_params


class EvaluationRunRecord(BaseModel):
    """Runtime snapshot of an evaluation run including lifecycle state."""

    model_config = ConfigDict(frozen=True)

    run_id: str
    name: str
    status: EvaluationRunStatus = Field(default=EvaluationRunStatus.PENDING)
    config: EvaluationRunConfig
    total_cases: int = 0
    completed_cases: int = 0
    failed_cases: int = 0
    started_at: datetime | None = None
    completed_at: datetime | None = None
    error_message: str | None = None
    metrics: AggregateMetrics | None = None
