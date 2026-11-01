"""Mathematical correctness and logical reasoning evaluators."""

import math
import re
from typing import Any

from src.evalforge.evaluators.base import BaseEvaluator, MetricResult


def extract_numeric_value(text: str) -> float | None:
    """Extract final numeric answer, fraction, or boxed value from text."""
    # Check for boxed LaTeX: \boxed{123} or \boxed{3/4}
    boxed = re.search(r"\\boxed\{([^\}]+)\}", text)
    if boxed:
        target = boxed.group(1).strip()
    else:
        # Check for explicitly labeled answer: Answer: 3/4 or Result: 42
        ans = re.search(
            r"(?:answer|result|final answer)[:=\s]+([+-]?\d+(?:\.\d+)?(?:\s*/\s*[+-]?\d+(?:\.\d+)?)?)",
            text,
            re.IGNORECASE,
        )
        if ans:
            target = ans.group(1).strip()
        else:
            # Check for standalone fraction: e.g. 3/4
            frac = re.search(r"\b([+-]?\d+(?:\.\d+)?\s*/\s*[+-]?\d+(?:\.\d+)?)\b", text)
            if frac:
                target = frac.group(1).strip()
            else:
                # Fallback to last number in string
                nums = re.findall(r"[+-]?(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?", text)
                if nums:
                    target = nums[-1]
                else:
                    return None

    # Handle simple fractions like 3/4
    if "/" in target:
        parts = target.split("/")
        if len(parts) == 2:
            try:
                num = float(parts[0].strip())
                den = float(parts[1].strip())
                return num / den if den != 0 else None
            except ValueError:
                pass

    try:
        return float(target)
    except ValueError:
        return None


class MathCorrectnessEvaluator(BaseEvaluator):
    """Evaluates mathematical correctness using numeric extraction and relative/absolute tolerance."""

    evaluator_id: str = "math_correctness"
    name: str = "math_correctness"
    version: str = "1.0.0"
    is_deterministic: bool = True
    required_inputs: list[str] = ["prediction", "reference"]

    def __init__(self, rel_tol: float = 1e-4, abs_tol: float = 1e-4, **kwargs: Any) -> None:
        super().__init__(
            name="math_correctness",
            evaluator_id="math_correctness",
            description="Numeric and mathematical answer extraction with tolerance comparison.",
            **kwargs,
        )
        self.rel_tol = rel_tol
        self.abs_tol = abs_tol

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
                method="numeric_tolerance",
                details={"error": "Reference answer is required"},
            )

        pred_val = extract_numeric_value(str(prediction))
        ref_val = extract_numeric_value(str(reference))

        if pred_val is None or ref_val is None:
            # Fallback to normalized exact match if non-numeric
            match = str(prediction).strip().lower() == str(reference).strip().lower()
            return MetricResult(
                name=self.name,
                score=1.0 if match else 0.0,
                passed=match,
                method="text_match_fallback",
                details={
                    "extracted_prediction_numeric": pred_val,
                    "extracted_reference_numeric": ref_val,
                },
            )

        is_close = math.isclose(pred_val, ref_val, rel_tol=self.rel_tol, abs_tol=self.abs_tol)
        score = 1.0 if is_close else 0.0

        return MetricResult(
            name=self.name,
            score=score,
            passed=is_close,
            method="numeric_math_tolerance",
            details={
                "predicted_val": pred_val,
                "reference_val": ref_val,
                "abs_diff": abs(pred_val - ref_val),
                "is_close": is_close,
            },
        )


class ConstraintSatisfactionEvaluator(BaseEvaluator):
    """Verifies that model output satisfies explicit formatting and constraint rules."""

    evaluator_id: str = "constraint_satisfaction"
    name: str = "constraint_satisfaction"
    version: str = "1.0.0"
    is_deterministic: bool = True
    required_inputs: list[str] = ["prediction"]

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(
            name="constraint_satisfaction",
            evaluator_id="constraint_satisfaction",
            description="Verifies logical and formatting constraints such as word limits, forbidden words, and prefixes.",
            **kwargs,
        )

    async def evaluate(
        self,
        prediction: str,
        reference: str | None = None,
        context: str | None = None,
        max_words: int | None = None,
        min_words: int | None = None,
        must_start_with: str | None = None,
        forbidden_terms: list[str] | None = None,
        **kwargs: Any,
    ) -> MetricResult:
        pred_str = str(prediction).strip()
        words = pred_str.split()
        violations: list[str] = []

        if max_words is not None and len(words) > max_words:
            violations.append(f"Exceeded max word count: {len(words)} > {max_words}")

        if min_words is not None and len(words) < min_words:
            violations.append(f"Below min word count: {len(words)} < {min_words}")

        if must_start_with is not None and not pred_str.lower().startswith(must_start_with.lower()):
            violations.append(f"Must start with '{must_start_with}'")

        if forbidden_terms:
            for term in forbidden_terms:
                if term.lower() in pred_str.lower():
                    violations.append(f"Contains forbidden term: '{term}'")

        passed = len(violations) == 0
        score = 1.0 if passed else 0.0

        return MetricResult(
            name=self.name,
            score=score,
            passed=passed,
            method="constraint_rule_checking",
            details={
                "word_count": len(words),
                "violations": violations,
            },
        )


__all__ = [
    "MathCorrectnessEvaluator",
    "ConstraintSatisfactionEvaluator",
    "extract_numeric_value",
]
