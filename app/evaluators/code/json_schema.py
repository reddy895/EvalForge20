"""JSON Schema compliance evaluator."""

import json
from typing import Any

import jsonschema

from app.domain.contracts import EvaluatorContract, EvaluatorInput
from app.domain.results import MetricResult
from app.evaluators.code.json_validity import extract_json_payload
from app.evaluators.registry import MetricCategory, MetricDefinition, registry


class JSONSchemaEvaluator(EvaluatorContract):
    """Evaluates whether system output conforms to a specified JSON Schema."""

    @property
    def metric_id(self) -> str:
        return "json_schema"

    @property
    def metric_name(self) -> str:
        return "JSON Schema Validity"

    async def evaluate(self, eval_input: EvaluatorInput) -> MetricResult:
        actual = eval_input.actual_output
        schema: dict[str, Any] | None = eval_input.options.get(
            "schema"
        ) or eval_input.case.metadata.get("schema")

        if not schema:
            return MetricResult(
                metric_id=self.metric_id,
                metric_name=self.metric_name,
                score=None,
                passed=None,
                reason="No schema specified in options or case metadata",
                details={"status": "skipped_no_schema"},
                is_model_based=False,
            )

        if actual is None:
            return MetricResult(
                metric_id=self.metric_id,
                metric_name=self.metric_name,
                score=0.0,
                passed=False,
                reason="Output is empty or None",
                details={"error": "empty_output"},
                is_model_based=False,
            )

        # Parse JSON payload
        if isinstance(actual, dict | list):
            parsed = actual
        else:
            extracted = extract_json_payload(str(actual))
            try:
                parsed = json.loads(extracted)
            except json.JSONDecodeError as exc:
                return MetricResult(
                    metric_id=self.metric_id,
                    metric_name=self.metric_name,
                    score=0.0,
                    passed=False,
                    reason=f"Cannot validate schema: output is not valid JSON ({exc.msg})",
                    details={"error": str(exc)},
                    is_model_based=False,
                )

        # Validate against JSON schema with comprehensive error aggregation
        try:
            validator = jsonschema.Draft7Validator(schema)
            errors = list(validator.iter_errors(parsed))
            if not errors:
                return MetricResult(
                    metric_id=self.metric_id,
                    metric_name=self.metric_name,
                    score=1.0,
                    passed=True,
                    reason="Output satisfies all JSON schema constraints",
                    details={"schema_title": schema.get("title", "unnamed"), "violations_count": 0},
                    is_model_based=False,
                )

            violations: list[dict[str, Any]] = []
            for err in errors[:10]:
                path_str = ".".join(str(p) for p in err.path) if err.path else "root"
                violations.append(
                    {
                        "path": path_str,
                        "message": err.message,
                        "validator": err.validator,
                    }
                )

            primary_err = violations[0]
            first_path = primary_err["path"]
            first_msg = primary_err["message"]

            return MetricResult(
                metric_id=self.metric_id,
                metric_name=self.metric_name,
                score=0.0,
                passed=False,
                reason=f"Schema violation: found {len(errors)} violation(s). First at '{first_path}': {first_msg}",
                details={
                    "violations": violations,
                    "total_violations": len(errors),
                    "schema_title": schema.get("title", "unnamed"),
                },
                is_model_based=False,
            )
        except jsonschema.SchemaError as exc:
            return MetricResult(
                metric_id=self.metric_id,
                metric_name=self.metric_name,
                score=None,
                passed=None,
                reason=f"Invalid target schema definition: {exc.message}",
                details={"schema_error": str(exc)},
                is_model_based=False,
            )


registry.register(
    JSONSchemaEvaluator,
    MetricDefinition(
        metric_id="json_schema",
        metric_name="JSON Schema Validity",
        description="Validates structured model output against a defined JSON schema using jsonschema.",
        category=MetricCategory.DETERMINISTIC,
        requires_expected_output=False,
    ),
)
