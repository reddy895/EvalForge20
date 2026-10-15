"""Contracts and protocols for model providers and evaluators."""

from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.domain.models import EvaluationCase
from app.domain.results import MetricResult


class ProviderRequest(BaseModel):
    """Normalized request passed to an AI model provider."""

    model_config = ConfigDict(frozen=True)

    prompt: str = Field(..., description="The user or task prompt string")
    system_prompt: str | None = Field(default=None)
    temperature: float = Field(default=0.0, ge=0.0, le=2.0)
    max_tokens: int | None = Field(default=None, gt=0)
    stop_sequences: list[str] | None = Field(default=None)
    response_format: str | None = Field(default=None, description="e.g. 'json' for JSON mode")
    tools: list[dict[str, Any]] | None = Field(default=None)
    extra_params: dict[str, Any] = Field(default_factory=dict)


class ProviderResponse(BaseModel):
    """Normalized response returned by an AI model provider."""

    model_config = ConfigDict(frozen=True)

    output_text: str | None = Field(default=None)
    latency_ms: float = Field(default=0.0, ge=0.0)
    token_usage: dict[str, int] | None = Field(default=None)
    raw_response: dict[str, Any] | None = Field(default=None)
    error_category: str | None = Field(default=None)
    error_message: str | None = Field(default=None)
    is_success: bool = Field(default=True)


class EvaluatorInput(BaseModel):
    """Standardized input context passed into an evaluator."""

    model_config = ConfigDict(frozen=True)

    case: EvaluationCase
    actual_output: str | dict[str, Any] | None = Field(default=None)
    options: dict[str, Any] = Field(default_factory=dict)


class ProviderContract(ABC):
    """Abstract interface that all model providers must implement."""

    @abstractmethod
    async def generate(self, request: ProviderRequest) -> ProviderResponse:
        """Execute a prompt generation request."""
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """Verify provider availability and connectivity."""
        pass


class EvaluatorContract(ABC):
    """Abstract interface for all evaluators in EvalForge20."""

    @property
    @abstractmethod
    def metric_id(self) -> str:
        """Unique identifier for this evaluator metric."""
        pass

    @property
    @abstractmethod
    def metric_name(self) -> str:
        """Human-readable display name for this metric."""
        pass

    @abstractmethod
    async def evaluate(self, eval_input: EvaluatorInput) -> MetricResult:
        """Evaluate a test case and produce a MetricResult."""
        pass
