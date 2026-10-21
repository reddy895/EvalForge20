"""JSON Schema compliance and structured output verification evaluator."""

import json
import re
from typing import Any

from src.evalforge.evaluators.base import BaseEvaluator, MetricResult


class JsonSchemaEvaluator(BaseEvaluator):
    """Evaluates whether model output satisfies valid JSON syntax and strict schema rules."""

    name = "json_schema_compliance"
    version = "1.0.0"
    is_deterministic = True

    @staticmethod
    def extract_json_str(text: str) -> str:
        """Extract JSON substring, stripping markdown code fences if present."""
        clean = text.strip()
        # Look for ```json ... ``` or ``` ... ```
        fence_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", clean, re.IGNORECASE)
        if fence_match:
            return fence_match.group(1).strip()
        # Look for first { or [ to last } or ]
        bracket_match = re.search(r"(\{[\s\S]*\}|\[[\s\S]*\])", clean)
        if bracket_match:
            return bracket_match.group(1).strip()
        return clean

    async def evaluate(
        self,
        prediction: str,
        reference: str | None = None,
        context: str | None = None,
        schema: dict[str, Any] | None = None,
        required_fields: list[str] | None = None,
        **kwargs: Any,
    ) -> MetricResult:
        json_str = self.extract_json_str(prediction)

        # 1. Syntax Check
        try:
            parsed = json.loads(json_str)
        except Exception as exc:
            return MetricResult(
                name=self.name,
                score=0.0,
                passed=False,
                method="json_schema_validation",
                details={
                    "is_valid_json": False,
                    "error": f"Failed to parse JSON: {exc}",
                    "extracted_snippet": json_str[:150],
                },
            )

        # 2. Schema / Field Check
        req_fields = list(required_fields or [])
        if schema and "required" in schema and isinstance(schema["required"], list):
            req_fields.extend(schema["required"])
        req_fields = list(set(req_fields))

        missing_fields: list[str] = []
        type_errors: list[str] = []

        if isinstance(parsed, dict):
            for field in req_fields:
                if field not in parsed:
                    missing_fields.append(field)

            # Check property types if schema specified
            if schema and "properties" in schema and isinstance(schema["properties"], dict):
                for prop_name, prop_def in schema["properties"].items():
                    if prop_name in parsed and "type" in prop_def:
                        expected_type = prop_def["type"]
                        val = parsed[prop_name]
                        if expected_type == "string" and not isinstance(val, str):
                            type_errors.append(
                                f"Property '{prop_name}' expected string, got {type(val).__name__}"
                            )
                        elif expected_type == "integer" and (
                            not isinstance(val, int) or isinstance(val, bool)
                        ):
                            type_errors.append(
                                f"Property '{prop_name}' expected int, got {type(val).__name__}"
                            )
                        elif expected_type == "number" and not isinstance(val, (int, float)):
                            type_errors.append(
                                f"Property '{prop_name}' expected number, got {type(val).__name__}"
                            )
                        elif expected_type == "boolean" and not isinstance(val, bool):
                            type_errors.append(
                                f"Property '{prop_name}' expected boolean, got {type(val).__name__}"
                            )
                        elif expected_type == "array" and not isinstance(val, list):
                            type_errors.append(
                                f"Property '{prop_name}' expected array, got {type(val).__name__}"
                            )
                        elif expected_type == "object" and not isinstance(val, dict):
                            type_errors.append(
                                f"Property '{prop_name}' expected object, got {type(val).__name__}"
                            )
        elif req_fields:
            missing_fields.extend(req_fields)

        has_schema_issues = bool(missing_fields or type_errors)
        passed = not has_schema_issues
        score = (
            1.0 if passed else 0.5
        )  # Valid JSON gets partial credit, full schema compliance gets 1.0

        return MetricResult(
            name=self.name,
            score=score,
            passed=passed,
            method="json_schema_validation",
            details={
                "is_valid_json": True,
                "missing_fields": missing_fields,
                "type_errors": type_errors,
                "parsed_keys": list(parsed.keys()) if isinstance(parsed, dict) else [],
            },
        )
