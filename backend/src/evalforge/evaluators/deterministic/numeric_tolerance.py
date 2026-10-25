"""Numeric tolerance evaluator for mathematical word problems and arithmetic reasoning."""

import re
from typing import Any

from src.evalforge.evaluators.base import BaseEvaluator, EvaluationResult


class NumericToleranceEvaluator(BaseEvaluator):
    """Evaluates numerical answers with relative and absolute tolerance."""

    def __init__(self, atol: float = 1e-3, rtol: float = 1e-3):
        super().__init__(
            name="numeric_tolerance",
            description="Verifies numerical accuracy within specified tolerance bands.",
        )
        self.atol = atol
        self.rtol = rtol

    @staticmethod
    def _extract_numbers(text: str) -> list[float]:
        """Extract all float numbers from text."""
        # Find all integer or float numbers (including negatives)
        tokens = re.findall(r"[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?", text)
        numbers = []
        for t in tokens:
            try:
                numbers.append(float(t))
            except ValueError:
                pass
        return numbers

    async def evaluate(
        self,
        prediction: str,
        reference: str | None = None,
        context: str | None = None,
        **kwargs: Any,
    ) -> EvaluationResult:
        if not reference and not kwargs.get("expected_value"):
            return EvaluationResult(
                name=self.name,
                score=0.0,
                passed=False,
                method="numeric_extraction",
                details={"error": "No expected reference value provided for numerical assertion."},
            )

        ref_str = str(kwargs.get("expected_value") or reference).strip()
        ref_numbers = self._extract_numbers(ref_str)
        if not ref_numbers:
            return EvaluationResult(
                name=self.name,
                score=0.0,
                passed=False,
                method="numeric_extraction",
                details={"error": f"Could not parse reference number from '{ref_str}'."},
            )

        expected_val = ref_numbers[-1]
        pred_numbers = self._extract_numbers(prediction)

        if not pred_numbers:
            return EvaluationResult(
                name=self.name,
                score=0.0,
                passed=False,
                method="numeric_extraction",
                details={"error": "No numeric values found in model response.", "extracted": []},
            )

        # Check if the expected value appears anywhere in extracted numbers
        matched = False
        closest_diff = float("inf")
        closest_val = None

        for n in pred_numbers:
            diff = abs(n - expected_val)
            if diff < closest_diff:
                closest_diff = diff
                closest_val = n
            tolerance = self.atol + self.rtol * abs(expected_val)
            if diff <= tolerance:
                matched = True
                break

        return EvaluationResult(
            name=self.name,
            score=1.0 if matched else 0.0,
            passed=matched,
            method="numeric_tolerance_comparison",
            details={
                "expected": expected_val,
                "closest_extracted": closest_val,
                "difference": closest_diff,
                "all_extracted": pred_numbers,
                "tolerance": self.atol + self.rtol * abs(expected_val),
            },
        )
