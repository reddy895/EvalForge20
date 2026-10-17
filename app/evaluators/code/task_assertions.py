import json
import re
from typing import Any

from app.domain.contracts import EvaluatorContract, EvaluatorInput
from app.domain.results import MetricResult
from app.evaluators.code.json_validity import extract_json_payload
from app.evaluators.registry import MetricCategory, MetricDefinition, registry


class TaskAssertionEvaluator(EvaluatorContract):
    """Evaluates output against declarative predefined assertions without executing arbitrary code."""

    @property
    def metric_id(self) -> str:
        return "task_assertions"

    @property
    def metric_name(self) -> str:
        return "Task Assertions"

    async def evaluate(self, eval_input: EvaluatorInput) -> MetricResult:
        actual = eval_input.actual_output
        assertions: list[dict[str, Any]] | None = eval_input.options.get(
            "assertions"
        ) or eval_input.case.metadata.get("assertions")

        if not assertions:
            return MetricResult(
                metric_id=self.metric_id,
                metric_name=self.metric_name,
                score=None,
                passed=None,
                reason="No assertions specified in options or case metadata",
                details={"status": "skipped_no_assertions"},
                is_model_based=False,
            )

        text = "" if actual is None else str(actual)
        results: list[dict[str, Any]] = []
        passed_count = 0

        for idx, assertion in enumerate(assertions, start=1):
            assert_type = assertion.get("type", "").lower()
            val = assertion.get("value")
            name = assertion.get("name", f"assertion_{idx}")
            case_sensitive = assertion.get("case_sensitive", False)

            check_text = text if case_sensitive else text.lower()
            passed = False
            message = ""

            if assert_type == "contains_all":
                items = val if isinstance(val, list) else [str(val)]
                missing = [
                    item
                    for item in items
                    if (item if case_sensitive else item.lower()) not in check_text
                ]
                passed = len(missing) == 0
                message = (
                    f"Contains all required tokens ({items})"
                    if passed
                    else f"Missing required tokens: {missing}"
                )

            elif assert_type == "contains_any":
                items = val if isinstance(val, list) else [str(val)]
                found = [
                    item
                    for item in items
                    if (item if case_sensitive else item.lower()) in check_text
                ]
                passed = len(found) > 0
                message = f"Found matching tokens: {found}" if passed else f"None of {items} found"

            elif assert_type == "not_contains":
                items = val if isinstance(val, list) else [str(val)]
                forbidden = [
                    item
                    for item in items
                    if (item if case_sensitive else item.lower()) in check_text
                ]
                passed = len(forbidden) == 0
                message = (
                    "No prohibited tokens present"
                    if passed
                    else f"Contained prohibited tokens: {forbidden}"
                )

            elif assert_type == "regex_match":
                pattern = str(val)
                flags = 0 if case_sensitive else re.IGNORECASE
                try:
                    passed = bool(re.search(pattern, text, flags=flags))
                    message = (
                        f"Regex pattern '{pattern}' matched"
                        if passed
                        else f"Regex pattern '{pattern}' did not match"
                    )
                except re.error as exc:
                    passed = False
                    message = f"Invalid regex pattern: {exc}"

            elif assert_type == "min_length":
                min_len = int(val)
                passed = len(text) >= min_len
                message = (
                    f"Length {len(text)} >= {min_len}"
                    if passed
                    else f"Length {len(text)} < {min_len}"
                )

            elif assert_type == "max_length":
                max_len = int(val)
                passed = len(text) <= max_len
                message = (
                    f"Length {len(text)} <= {max_len}"
                    if passed
                    else f"Length {len(text)} > {max_len}"
                )

            elif assert_type == "starts_with":
                prefix = str(val) if case_sensitive else str(val).lower()
                passed = check_text.startswith(prefix)
                message = f"Starts with '{val}'" if passed else f"Does not start with '{val}'"

            elif assert_type == "ends_with":
                suffix = str(val) if case_sensitive else str(val).lower()
                passed = check_text.endswith(suffix)
                message = f"Ends with '{val}'" if passed else f"Does not end with '{val}'"

            else:
                passed = False
                message = f"Unknown assertion type: {assert_type}"

            if passed:
                passed_count += 1

            results.append(
                {"name": name, "type": assert_type, "passed": passed, "message": message}
            )

        total = len(assertions)
        all_passed = passed_count == total
        score = passed_count / total if total > 0 else 0.0

        return MetricResult(
            metric_id=self.metric_id,
            metric_name=self.metric_name,
            score=round(score, 4),
            passed=all_passed,
            reason=f"Passed {passed_count}/{total} task assertions"
            if all_passed
            else f"Failed {total - passed_count}/{total} task assertions",
            details={"assertion_results": results, "total": total, "passed": passed_count},
            is_model_based=False,
        )


registry.register(
    TaskAssertionEvaluator,
    MetricDefinition(
        metric_id="task_assertions",
        metric_name="Task Assertions",
        description="Safe, rule-based declarative checks: contains, prohibited terms, regex, and length constraints.",
        category=MetricCategory.DETERMINISTIC,
        requires_expected_output=False,
    ),
)
