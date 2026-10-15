"""Evaluator registry and metric definition metadata."""

from enum import StrEnum
from typing import Any
from pydantic import BaseModel, ConfigDict, Field

from app.domain.contracts import EvaluatorContract
from app.domain.errors import EvaluatorError


class MetricCategory(StrEnum):
    """Broad categories for evaluation metrics."""

    DETERMINISTIC = "deterministic"
    MODEL_BASED = "model_based"
    RAG = "rag"
    AGENT = "agent"
    COMPOSITE = "composite"
    SUMMARY = "summary"


class MetricDefinition(BaseModel):
    """Metadata specification for a registered evaluation metric."""

    model_config = ConfigDict(frozen=True)

    metric_id: str = Field(..., description="Stable unique identifier (e.g. 'exact_match')")
    metric_name: str = Field(..., description="Human-readable title (e.g. 'Exact Match')")
    description: str = Field(..., description="Detailed description of what the metric measures")
    category: MetricCategory = Field(default=MetricCategory.DETERMINISTIC)
    requires_expected_output: bool = Field(default=False)
    valid_range: tuple[float, float] = Field(default=(0.0, 1.0))
    options_schema: dict[str, Any] = Field(default_factory=dict)


class EvaluatorRegistry:
    """Central registry for discovering and instantiating evaluators."""

    def __init__(self) -> None:
        self._evaluators: dict[str, type[EvaluatorContract]] = {}
        self._definitions: dict[str, MetricDefinition] = {}

    def register(
        self,
        evaluator_cls: type[EvaluatorContract],
        definition: MetricDefinition,
    ) -> None:
        """Register an evaluator class and its metric definition."""
        self._evaluators[definition.metric_id] = evaluator_cls
        self._definitions[definition.metric_id] = definition

    def get(self, metric_id: str) -> EvaluatorContract:
        """Instantiate and return an evaluator by metric_id."""
        if metric_id not in self._evaluators:
            available = ", ".join(sorted(self._evaluators.keys()))
            raise EvaluatorError(
                f"Unknown metric '{metric_id}'. Available metrics: [{available}]",
                metric_id=metric_id,
            )
        evaluator_cls = self._evaluators[metric_id]
        return evaluator_cls()

    def get_definition(self, metric_id: str) -> MetricDefinition:
        """Retrieve the metric definition metadata for a given metric_id."""
        if metric_id not in self._definitions:
            raise EvaluatorError(
                f"Metric definition not found for '{metric_id}'",
                metric_id=metric_id,
            )
        return self._definitions[metric_id]

    def list_metrics(self) -> list[MetricDefinition]:
        """Return all registered metric definitions."""
        return list(self._definitions.values())

    def is_registered(self, metric_id: str) -> bool:
        """Check if a metric_id is currently registered."""
        return metric_id in self._evaluators


# Global registry singleton instance
registry = EvaluatorRegistry()
