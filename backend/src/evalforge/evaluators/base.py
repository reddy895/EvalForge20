"""Base metric interface, evaluation result schema, and metric registry."""

from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel, Field


class MetricResult(BaseModel):
    """Normalized output produced by any evaluation metric."""

    name: str = Field(..., description="Unique metric identifier")
    score: float = Field(
        ..., description="Normalized score (typically 0.0 - 1.0) or numeric quantity"
    )
    passed: bool = Field(..., description="Boolean pass/fail assertion based on threshold")
    method: str = Field(..., description="Explicit description of calculation methodology")
    details: dict[str, Any] = Field(
        default_factory=dict, description="Audit evidence and diagnostic details"
    )


EvaluationResult = MetricResult


class BaseEvaluator(ABC):
    """Abstract contract that all deterministic and model-assisted metrics adhere to."""

    name: str = "base"
    version: str = "1.0.0"
    is_deterministic: bool = True

    def __init__(
        self,
        name: str | None = None,
        description: str | None = None,
        **kwargs: Any,
    ) -> None:
        if name:
            self.name = name
        self.description = description or ""

    @abstractmethod
    async def evaluate(
        self,
        prediction: str,
        reference: str | None = None,
        context: str | None = None,
        **kwargs: Any,
    ) -> MetricResult:
        """Score candidate prediction against reference target or task rules."""
        pass


class MetricRegistry:
    """Registry coordinating available evaluation metrics."""

    def __init__(self) -> None:
        self._evaluators: dict[str, BaseEvaluator] = {}

    def register(self, evaluator: BaseEvaluator) -> None:
        self._evaluators[evaluator.name.lower()] = evaluator

    def get(self, name: str) -> BaseEvaluator | None:
        return self._evaluators.get(name.lower())

    def list_metrics(self) -> list[str]:
        return sorted(self._evaluators.keys())


_metric_registry: MetricRegistry | None = None


def get_metric_registry() -> MetricRegistry:
    """Return shared metric registry instance."""
    global _metric_registry
    if _metric_registry is None:
        _metric_registry = MetricRegistry()
    return _metric_registry
