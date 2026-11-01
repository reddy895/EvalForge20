"""Structured output, JSON validity, and schema compliance evaluators."""

import json
from typing import Any

from src.evalforge.evaluators.base import BaseEvaluator, MetricResult
from src.evalforge.evaluators.deterministic.json_schema import JsonSchemaEvaluator


class JsonValidityEvaluator(BaseEvaluator):
    """Evaluates whether output parses into valid RFC 8259 JSON."""

    evaluator_id: str = "json_validity"
    name: str = "json_validity"
    version: str = "1.0.0"
    is_deterministic: bool = True
    required_inputs: list[str] = ["prediction"]

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(
            name="json_validity",
            evaluator_id="json_validity",
            description="Verifies that model output contains well-formed, parseable JSON syntax.",
            **kwargs,
        )

    async def evaluate(
        self,
        prediction: str,
        reference: str | None = None,
        context: str | None = None,
        **kwargs: Any,
    ) -> MetricResult:
        json_str = JsonSchemaEvaluator.extract_json_str(str(prediction))
        try:
            parsed = json.loads(json_str)
            return MetricResult(
                name=self.name,
                score=1.0,
                passed=True,
                method="json_parse_verification",
                details={
                    "is_valid": True,
                    "root_type": type(parsed).__name__,
                },
            )
        except Exception as exc:
            return MetricResult(
                name=self.name,
                score=0.0,
                passed=False,
                method="json_parse_verification",
                details={
                    "is_valid": False,
                    "error": str(exc),
                },
            )


__all__ = [
    "JsonValidityEvaluator",
    "JsonSchemaEvaluator",
]
