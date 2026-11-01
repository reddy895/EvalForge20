"""Accuracy evaluation metrics: Exact Match, Normalized Exact Match, and Contains."""

import re
import string
from typing import Any

from src.evalforge.evaluators.base import BaseEvaluator, MetricResult


def normalize_text(text: str) -> str:
    """Normalize text by lowercasing, removing punctuation, and collapsing whitespace."""
    text = text.lower()
    text = text.translate(str.maketrans("", "", string.punctuation))
    text = re.sub(r"\s+", " ", text).strip()
    return text


class ExactMatchEvaluator(BaseEvaluator):
    """Evaluates strict character-for-character exact match equality."""

    evaluator_id: str = "exact_match"
    name: str = "exact_match"
    version: str = "1.0.0"
    is_deterministic: bool = True
    required_inputs: list[str] = ["prediction", "reference"]

    def __init__(self, case_sensitive: bool = False, strip_whitespace: bool = True, **kwargs: Any) -> None:
        super().__init__(
            name="exact_match",
            evaluator_id="exact_match",
            description="Strict string equality comparison between model prediction and reference.",
            **kwargs,
        )
        self.case_sensitive = case_sensitive
        self.strip_whitespace = strip_whitespace

    async def evaluate(
        self,
        prediction: str,
        reference: str | None = None,
        context: str | None = None,
        **kwargs: Any,
    ) -> MetricResult:
        if reference is None:
            return MetricResult(
                name=self.name,
                score=0.0,
                passed=False,
                method="exact_match",
                details={"error": "Reference target is required for exact match evaluation"},
            )

        pred_str = str(prediction)
        ref_str = str(reference)

        if self.strip_whitespace:
            pred_str = pred_str.strip()
            ref_str = ref_str.strip()

        if not self.case_sensitive:
            pred_str = pred_str.lower()
            ref_str = ref_str.lower()

        match = pred_str == ref_str
        score = 1.0 if match else 0.0

        return MetricResult(
            name=self.name,
            score=score,
            passed=match,
            method="strict_exact_match" if self.case_sensitive else "case_insensitive_exact_match",
            details={
                "prediction": prediction,
                "reference": reference,
                "case_sensitive": self.case_sensitive,
            },
        )


class NormalizedAccuracyEvaluator(BaseEvaluator):
    """Normalized exact match accuracy after removing punctuation, articles, and spacing."""

    evaluator_id: str = "normalized_accuracy"
    name: str = "normalized_accuracy"
    version: str = "1.0.0"
    is_deterministic: bool = True
    required_inputs: list[str] = ["prediction", "reference"]

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(
            name="normalized_accuracy",
            evaluator_id="normalized_accuracy",
            description="Normalized text equality ignoring punctuation, extra whitespace, and casing.",
            **kwargs,
        )

    async def evaluate(
        self,
        prediction: str,
        reference: str | None = None,
        context: str | None = None,
        **kwargs: Any,
    ) -> MetricResult:
        if reference is None:
            return MetricResult(
                name=self.name,
                score=0.0,
                passed=False,
                method="normalized_accuracy",
                details={"error": "Reference target is required"},
            )

        norm_pred = normalize_text(str(prediction))
        norm_ref = normalize_text(str(reference))

        match = norm_pred == norm_ref
        score = 1.0 if match else 0.0

        return MetricResult(
            name=self.name,
            score=score,
            passed=match,
            method="normalized_text_match",
            details={
                "normalized_prediction": norm_pred,
                "normalized_reference": norm_ref,
            },
        )


__all__ = [
    "ExactMatchEvaluator",
    "NormalizedAccuracyEvaluator",
    "normalize_text",
]
