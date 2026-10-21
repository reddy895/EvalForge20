"""Exact Match and Case-Normalized Exact Match deterministic metrics."""

import re
import string
from typing import Any, Optional

from src.evalforge.evaluators.base import BaseEvaluator, MetricResult


class ExactMatchEvaluator(BaseEvaluator):
    """Strict character-level equality check between prediction and reference answer."""

    name = "exact_match"
    version = "1.0.0"
    is_deterministic = True

    async def evaluate(
        self,
        prediction: str,
        reference: Optional[str] = None,
        context: Optional[str] = None,
        **kwargs: Any,
    ) -> MetricResult:
        if reference is None:
            return MetricResult(
                name=self.name,
                score=0.0,
                passed=False,
                method="strict_string_equality",
                details={"reason": "No reference output provided for exact match."},
            )

        pred_clean = prediction.strip()
        ref_clean = reference.strip()
        is_match = pred_clean == ref_clean

        return MetricResult(
            name=self.name,
            score=1.0 if is_match else 0.0,
            passed=is_match,
            method="strict_string_equality",
            details={
                "prediction_length": len(pred_clean),
                "reference_length": len(ref_clean),
                "matched": is_match,
            },
        )


class NormalizedExactMatchEvaluator(BaseEvaluator):
    """Robust normalized exact match removing punctuation, casing differences, and filler articles."""

    name = "normalized_exact_match"
    version = "1.0.0"
    is_deterministic = True

    @staticmethod
    def normalize_text(s: str) -> str:
        """Lowercase, remove punctuation, strip articles, and collapse repeated whitespaces."""
        s = s.lower()
        # Remove punctuation
        s = "".join(ch for ch in s if ch not in set(string.punctuation))
        # Remove articles
        s = re.sub(r"\b(a|an|the)\b", " ", s)
        # Collapse whitespace
        s = " ".join(s.split())
        return s.strip()

    async def evaluate(
        self,
        prediction: str,
        reference: Optional[str] = None,
        context: Optional[str] = None,
        **kwargs: Any,
    ) -> MetricResult:
        if reference is None:
            return MetricResult(
                name=self.name,
                score=0.0,
                passed=False,
                method="normalized_text_equality",
                details={"reason": "No reference output provided for normalized match."},
            )

        norm_pred = self.normalize_text(prediction)
        norm_ref = self.normalize_text(reference)
        is_match = norm_pred == norm_ref

        return MetricResult(
            name=self.name,
            score=1.0 if is_match else 0.0,
            passed=is_match,
            method="normalized_text_equality",
            details={
                "normalized_prediction": norm_pred,
                "normalized_reference": norm_ref,
                "matched": is_match,
            },
        )
