"""Normalized text and value match evaluator."""

import re
import string
from typing import Any

from app.domain.contracts import EvaluatorContract, EvaluatorInput
from app.domain.results import MetricResult
from app.evaluators.registry import MetricCategory, MetricDefinition, registry


def normalize_text(
    text: Any,
    lowercase: bool = True,
    strip_punctuation: bool = True,
    collapse_whitespace: bool = True,
    normalize_numbers: bool = True,
) -> str:
    """Normalize input into a canonical text string for comparison."""
    if text is None:
        return ""

    s = str(text)

    if lowercase:
        s = s.lower()

    if strip_punctuation:
        # Remove ASCII punctuation
        translator = str.maketrans("", "", string.punctuation)
        s = s.translate(translator)

    if collapse_whitespace:
        s = re.sub(r"\s+", " ", s).strip()

    if normalize_numbers:
        # Convert floating point representations like 42.0 to 42 when equivalent
        try:
            val = float(s)
            if val.is_integer():
                s = str(int(val))
        except ValueError:
            pass

    return s


class NormalizedMatchEvaluator(EvaluatorContract):
    """Evaluates whether actual output matches expected reference after documented normalization."""

    @property
    def metric_id(self) -> str:
        return "normalized_match"

    @property
    def metric_name(self) -> str:
        return "Normalized Match"

    async def evaluate(self, eval_input: EvaluatorInput) -> MetricResult:
        expected = eval_input.case.expected_output
        actual = eval_input.actual_output
        opts = eval_input.options

        if expected is None:
            return MetricResult(
                metric_id=self.metric_id,
                metric_name=self.metric_name,
                score=None,
                passed=None,
                reason="No expected_output defined for this test case",
                details={"status": "skipped_no_reference"},
                is_model_based=False,
            )

        if actual is None:
            return MetricResult(
                metric_id=self.metric_id,
                metric_name=self.metric_name,
                score=0.0,
                passed=False,
                reason="Actual output is missing or empty",
                details={"actual": None, "expected": str(expected)},
                is_model_based=False,
            )

        norm_actual = normalize_text(
            actual,
            lowercase=opts.get("lowercase", True),
            strip_punctuation=opts.get("strip_punctuation", True),
            collapse_whitespace=opts.get("collapse_whitespace", True),
            normalize_numbers=opts.get("normalize_numbers", True),
        )
        norm_expected = normalize_text(
            expected,
            lowercase=opts.get("lowercase", True),
            strip_punctuation=opts.get("strip_punctuation", True),
            collapse_whitespace=opts.get("collapse_whitespace", True),
            normalize_numbers=opts.get("normalize_numbers", True),
        )

        is_match = norm_actual == norm_expected
        return MetricResult(
            metric_id=self.metric_id,
            metric_name=self.metric_name,
            score=1.0 if is_match else 0.0,
            passed=is_match,
            reason="Normalized output matches reference" if is_match else "Normalized output differs from reference",
            details={
                "normalized_actual": norm_actual,
                "normalized_expected": norm_expected,
            },
            is_model_based=False,
        )


registry.register(
    NormalizedMatchEvaluator,
    MetricDefinition(
        metric_id="normalized_match",
        metric_name="Normalized Match",
        description="Compares actual and reference outputs after case-folding, whitespace trimming, and punctuation normalization.",
        category=MetricCategory.DETERMINISTIC,
        requires_expected_output=True,
    ),
)
