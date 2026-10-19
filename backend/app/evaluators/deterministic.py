"""Deterministic evaluators for string matching, keyword assertions, and JSON schemas."""

import json
import re
from typing import Any

from backend.app.schemas.evaluations import CaseMetricResult


class ExactMatchEvaluator:
    """Checks whether actual output matches expected string exactly."""

    @staticmethod
    def evaluate(actual: str, expected: str | None) -> CaseMetricResult:
        if not expected:
            return CaseMetricResult(metric_name="exact_match", passed=True, score=1.0)
        passed = actual.strip() == expected.strip()
        return CaseMetricResult(
            metric_name="exact_match",
            passed=passed,
            score=1.0 if passed else 0.0,
            details=None if passed else "Exact string mismatch",
        )


class NormalizedMatchEvaluator:
    """Normalizes whitespace and casing before comparison."""

    @staticmethod
    def evaluate(actual: str, expected: str | None) -> CaseMetricResult:
        if not expected:
            return CaseMetricResult(metric_name="normalized_match", passed=True, score=1.0)
        norm_actual = re.sub(r"\s+", " ", actual.strip().lower())
        norm_expected = re.sub(r"\s+", " ", expected.strip().lower())
        passed = norm_actual == norm_expected
        return CaseMetricResult(
            metric_name="normalized_match",
            passed=passed,
            score=1.0 if passed else 0.0,
            details=None if passed else "Normalized string mismatch",
        )


class KeywordContainsEvaluator:
    """Verifies that all specified assertion substrings or keywords are present."""

    @staticmethod
    def evaluate(actual: str, assertions: list[str]) -> CaseMetricResult:
        if not assertions:
            return CaseMetricResult(metric_name="assertions_passed", passed=True, score=1.0)
        missing = [a for a in assertions if a.lower() not in actual.lower()]
        passed = len(missing) == 0
        score = round((len(assertions) - len(missing)) / len(assertions), 4)
        return CaseMetricResult(
            metric_name="assertions_passed",
            passed=passed,
            score=score,
            details=f"Missing expected keywords: {missing}"
            if missing
            else "All assertions matched",
        )


class JsonValidityEvaluator:
    """Extracts and parses JSON object from model output."""

    @staticmethod
    def evaluate(actual: str) -> tuple[CaseMetricResult, dict[str, Any] | None]:
        # Try extracting JSON markdown block if present
        text = actual.strip()
        code_block = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
        if code_block:
            text = code_block.group(1).strip()
        else:
            first_brace = text.find("{")
            last_brace = text.rfind("}")
            if first_brace != -1 and last_brace != -1:
                text = text[first_brace : last_brace + 1]

        try:
            parsed = json.loads(text)
            if isinstance(parsed, dict):
                return CaseMetricResult(metric_name="json_validity", passed=True, score=1.0), parsed
            else:
                return (
                    CaseMetricResult(
                        metric_name="json_validity",
                        passed=False,
                        score=0.0,
                        details="JSON is not an object",
                    ),
                    None,
                )
        except Exception as exc:
            return (
                CaseMetricResult(
                    metric_name="json_validity",
                    passed=False,
                    score=0.0,
                    details=f"Invalid JSON: {exc}",
                ),
                None,
            )
