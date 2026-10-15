"""JSON validity evaluator."""

import json
import re
from typing import Any

from app.domain.contracts import EvaluatorContract, EvaluatorInput
from app.domain.results import MetricResult
from app.evaluators.registry import MetricCategory, MetricDefinition, registry


def extract_json_payload(text: str) -> str:
    """Extract raw JSON from possible markdown fenced code blocks or surrounding text."""
    stripped = text.strip()

    # Look for ```json ... ``` block
    match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", stripped, re.IGNORECASE)
    if match:
        return match.group(1).strip()

    # Look for bare object or array substring if surrounded by extra conversation
    brace_start = stripped.find("{")
    bracket_start = stripped.find("[")

    if brace_start != -1 and (bracket_start == -1 or brace_start < bracket_start):
        brace_end = stripped.rfind("}")
        if brace_end > brace_start:
            return stripped[brace_start : brace_end + 1]
    elif bracket_start != -1:
        bracket_end = stripped.rfind("]")
        if bracket_end > bracket_start:
            return stripped[bracket_start : bracket_end + 1]

    return stripped


class JSONValidityEvaluator(EvaluatorContract):
    """Evaluates whether system output parses as valid JSON syntax."""

    @property
    def metric_id(self) -> str:
        return "json_validity"

    @property
    def metric_name(self) -> str:
        return "JSON Validity"

    async def evaluate(self, eval_input: EvaluatorInput) -> MetricResult:
        actual = eval_input.actual_output

        if actual is None or (isinstance(actual, str) and not actual.strip()):
            return MetricResult(
                metric_id=self.metric_id,
                metric_name=self.metric_name,
                score=0.0,
                passed=False,
                reason="Output is empty or None",
                details={"error": "empty_output"},
                is_model_based=False,
            )

        if isinstance(actual, dict | list):
            # Already a structured dict/list
            return MetricResult(
                metric_id=self.metric_id,
                metric_name=self.metric_name,
                score=1.0,
                passed=True,
                reason="Output is valid structured JSON data",
                details={"parsed_type": type(actual).__name__},
                is_model_based=False,
            )

        raw_str = str(actual)
        extracted = extract_json_payload(raw_str)

        try:
            parsed: Any = json.loads(extracted)
            return MetricResult(
                metric_id=self.metric_id,
                metric_name=self.metric_name,
                score=1.0,
                passed=True,
                reason="Output is valid JSON",
                details={"parsed_type": type(parsed).__name__},
                is_model_based=False,
            )
        except json.JSONDecodeError as exc:
            return MetricResult(
                metric_id=self.metric_id,
                metric_name=self.metric_name,
                score=0.0,
                passed=False,
                reason=f"Failed to parse JSON: {exc.msg} (line {exc.lineno}, col {exc.colno})",
                details={"error": str(exc), "extracted_snippet": extracted[:200]},
                is_model_based=False,
            )


registry.register(
    JSONValidityEvaluator,
    MetricDefinition(
        metric_id="json_validity",
        metric_name="JSON Validity",
        description="Checks whether system output parses as valid JSON, extracting markdown codeblocks if necessary.",
        category=MetricCategory.DETERMINISTIC,
        requires_expected_output=False,
    ),
)
