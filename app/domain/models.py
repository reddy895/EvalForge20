"""Core domain entities and configuration models for EvalForge20."""

from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class TargetType(str, Enum):
    """Supported target system types."""

    LLM = "llm"
    OLLAMA = "ollama"
    RAG = "rag"
    AGENT = "agent"
    MOCK = "mock"


class TargetConfiguration(BaseModel):
    """Configuration for an evaluation target system."""

    model_config = ConfigDict(frozen=True)

    target_name: str = Field(..., min_length=1, description="Unique human-readable target name")
    target_type: TargetType = Field(default=TargetType.MOCK, description="Type of target system")
    provider_name: str = Field(default="mock", description="Provider adapter name (e.g. ollama, mock)")
    model_identifier: str = Field(default="mock-model-v1", description="Model identifier")
    base_url: str | None = Field(default=None, description="Custom base URL for the provider endpoint")
    temperature: float = Field(default=0.0, ge=0.0, le=2.0)
    max_tokens: int | None = Field(default=None, gt=0)
    timeout_seconds: float = Field(default=60.0, gt=0.0)
    extra_params: dict[str, Any] = Field(default_factory=dict)


class EvaluatorConfiguration(BaseModel):
    """Configuration for an evaluator invoked during a run."""

    model_config = ConfigDict(frozen=True)

    evaluator_name: str = Field(..., min_length=1, description="Evaluator identifier from registry")
    metric_id: str = Field(..., min_length=1, description="Unique metric identifier")
    weight: float = Field(default=1.0, ge=0.0, description="Relative weight in composite scoring")
    threshold: float | None = Field(default=None, description="Optional pass/fail score threshold")
    rubric_version: str | None = Field(default=None, description="Version of rubric if model-based")
    options: dict[str, Any] = Field(default_factory=dict, description="Custom evaluator options")


class EvaluationCase(BaseModel):
    """A single canonical test case within an evaluation dataset."""

    model_config = ConfigDict(frozen=True)

    id: str = Field(..., min_length=1, description="Stable test case identifier")
    input: str | dict[str, Any] = Field(..., description="Prompt text or structured input payload")
    expected_output: str | dict[str, Any] | None = Field(
        default=None, description="Optional ground-truth reference output"
    )
    metadata: dict[str, Any] = Field(default_factory=dict, description="Arbitrary case metadata")
    tags: list[str] = Field(default_factory=list, description="Categorical tags for filtering")
    category: str | None = Field(default=None, description="Optional primary category")
    # Domain-specific optional fields
    context: list[str] | None = Field(
        default=None, description="Reference contexts for RAG evaluation"
    )
    tools: list[dict[str, Any]] | None = Field(
        default=None, description="Tool definitions available to an agent"
    )
    expected_tool_calls: list[dict[str, Any]] | None = Field(
        default=None, description="Expected sequence of tool calls for agent evaluation"
    )
