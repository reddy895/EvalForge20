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

    evaluator_id: str = "base"
    name: str = "base"
    version: str = "1.0.0"
    is_deterministic: bool = True
    required_inputs: list[str] = ["prediction", "reference"]

    def __init__(
        self,
        name: str | None = None,
        evaluator_id: str | None = None,
        description: str | None = None,
        version: str = "1.0.0",
        is_deterministic: bool = True,
        required_inputs: list[str] | None = None,
        **kwargs: Any,
    ) -> None:
        if name:
            self.name = name
        if evaluator_id:
            self.evaluator_id = evaluator_id
        elif self.name and self.name != "base":
            self.evaluator_id = self.name
        else:
            self.evaluator_id = getattr(type(self), "evaluator_id", "base")
        self.description = description or ""
        self.version = version
        self.is_deterministic = is_deterministic
        if required_inputs is not None:
            self.required_inputs = required_inputs

    def validate(self, **kwargs: Any) -> list[str]:
        """Validate whether all required inputs are present for evaluation."""
        errors: list[str] = []
        for req in self.required_inputs:
            if req not in kwargs or kwargs[req] is None:
                errors.append(f"Evaluator '{self.name}' requires input '{req}'.")
        return errors

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

    def aggregate(self, results: list[MetricResult]) -> dict[str, Any]:
        """Aggregate a list of individual MetricResult objects into summary statistics."""
        if not results:
            return {
                "count": 0,
                "passed_count": 0,
                "pass_rate": 0.0,
                "mean_score": 0.0,
            }
        scores = [r.score for r in results]
        passed = sum(1 for r in results if r.passed)
        mean_score = sum(scores) / len(scores) if scores else 0.0
        pass_rate = passed / len(results) if results else 0.0
        return {
            "count": len(results),
            "passed_count": passed,
            "failed_count": len(results) - passed,
            "pass_rate": round(pass_rate, 4),
            "mean_score": round(mean_score, 4),
        }

    def serialize_result(self, result: MetricResult) -> dict[str, Any]:
        """Serialize a MetricResult into a standard dictionary format."""
        return result.model_dump()


class MetricRegistry:
    """Registry coordinating available evaluation metrics."""

    def __init__(self) -> None:
        self._evaluators: dict[str, BaseEvaluator] = {}

    def register(self, evaluator: BaseEvaluator) -> None:
        key = evaluator.evaluator_id.lower() if hasattr(evaluator, "evaluator_id") else evaluator.name.lower()
        self._evaluators[key] = evaluator
        self._evaluators[evaluator.name.lower()] = evaluator

    def get(self, name: str) -> BaseEvaluator | None:
        return self._evaluators.get(name.lower())

    def list_metrics(self) -> list[str]:
        return sorted(self._evaluators.keys())

    def list_evaluators(self) -> list[dict[str, Any]]:
        """List metadata for all registered evaluator plugins."""
        seen = set()
        items = []
        for ev in self._evaluators.values():
            eid = getattr(ev, "evaluator_id", ev.name)
            if eid in seen:
                continue
            seen.add(eid)
            items.append({
                "evaluator_id": eid,
                "name": ev.name,
                "version": ev.version,
                "description": getattr(ev, "description", ""),
                "is_deterministic": ev.is_deterministic,
                "required_inputs": ev.required_inputs,
            })
        return items


_metric_registry: MetricRegistry | None = None


def get_metric_registry() -> MetricRegistry:
    """Return shared metric registry instance populated with native deterministic metrics."""
    global _metric_registry
    if _metric_registry is None:
        reg = MetricRegistry()
        try:
            from src.evalforge.evaluators.deterministic.exact_match import (
                ExactMatchEvaluator,
                NormalizedExactMatchEvaluator,
            )
            from src.evalforge.evaluators.deterministic.token_f1 import TokenF1Evaluator
            from src.evalforge.evaluators.deterministic.keywords import KeywordEvaluator
            from src.evalforge.evaluators.deterministic.json_schema import JsonSchemaEvaluator
            from src.evalforge.evaluators.deterministic.code_execution import CodeExecutionEvaluator
            from src.evalforge.evaluators.deterministic.numeric_tolerance import NumericToleranceEvaluator
            from src.evalforge.evaluators.semantic import SemanticSimilarityEvaluator

            reg.register(ExactMatchEvaluator())
            reg.register(NormalizedExactMatchEvaluator())
            reg.register(TokenF1Evaluator())
            reg.register(KeywordEvaluator())
            reg.register(JsonSchemaEvaluator())
            reg.register(CodeExecutionEvaluator())
            reg.register(NumericToleranceEvaluator())
            reg.register(SemanticSimilarityEvaluator())
        except Exception:
            pass
        _metric_registry = reg
    return _metric_registry

