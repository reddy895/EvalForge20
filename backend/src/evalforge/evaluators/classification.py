"""Classification and token-level metrics: Precision, Recall, F1, and Categorical Accuracy."""

import re
import string
from collections import Counter
from typing import Any

from src.evalforge.evaluators.base import BaseEvaluator, MetricResult


def get_tokens(text: str) -> list[str]:
    """Normalize and tokenize text into words."""
    clean = text.lower().translate(str.maketrans("", "", string.punctuation))
    return re.sub(r"\s+", " ", clean).strip().split()


class TokenF1Evaluator(BaseEvaluator):
    """Calculates token-level precision, recall, and harmonic F1 score."""

    evaluator_id: str = "token_f1"
    name: str = "token_f1"
    version: str = "1.0.0"
    is_deterministic: bool = True
    required_inputs: list[str] = ["prediction", "reference"]

    def __init__(self, threshold: float = 0.5, **kwargs: Any) -> None:
        super().__init__(
            name="token_f1",
            evaluator_id="token_f1",
            description="Token-level precision, recall, and F1 score between prediction and reference.",
            **kwargs,
        )
        self.threshold = threshold

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
                method="token_f1",
                details={"error": "Reference target is required"},
            )

        pred_tokens = get_tokens(str(prediction))
        ref_tokens = get_tokens(str(reference))

        if not pred_tokens and not ref_tokens:
            return MetricResult(
                name=self.name,
                score=1.0,
                passed=True,
                method="token_f1",
                details={"precision": 1.0, "recall": 1.0, "f1": 1.0},
            )

        if not pred_tokens or not ref_tokens:
            return MetricResult(
                name=self.name,
                score=0.0,
                passed=False,
                method="token_f1",
                details={"precision": 0.0, "recall": 0.0, "f1": 0.0},
            )

        common = Counter(pred_tokens) & Counter(ref_tokens)
        num_same = sum(common.values())

        if num_same == 0:
            return MetricResult(
                name=self.name,
                score=0.0,
                passed=False,
                method="token_f1",
                details={"precision": 0.0, "recall": 0.0, "f1": 0.0},
            )

        precision = num_same / len(pred_tokens)
        recall = num_same / len(ref_tokens)
        f1 = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0

        return MetricResult(
            name=self.name,
            score=round(f1, 4),
            passed=f1 >= self.threshold,
            method="token_f1",
            details={
                "precision": round(precision, 4),
                "recall": round(recall, 4),
                "f1": round(f1, 4),
                "common_tokens_count": num_same,
            },
        )


class ClassificationAccuracyEvaluator(BaseEvaluator):
    """Categorical label classification accuracy evaluator."""

    evaluator_id: str = "classification_accuracy"
    name: str = "classification_accuracy"
    version: str = "1.0.0"
    is_deterministic: bool = True
    required_inputs: list[str] = ["prediction", "reference"]

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(
            name="classification_accuracy",
            evaluator_id="classification_accuracy",
            description="Categorical label match accuracy.",
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
                method="classification_accuracy",
                details={"error": "Reference is required"},
            )

        # Match exact extracted label
        clean_pred = str(prediction).strip().lower()
        clean_ref = str(reference).strip().lower()

        is_match = clean_pred == clean_ref or clean_ref in clean_pred.split()
        score = 1.0 if is_match else 0.0

        return MetricResult(
            name=self.name,
            score=score,
            passed=is_match,
            method="label_match",
            details={"prediction": prediction, "reference": reference},
        )


__all__ = [
    "TokenF1Evaluator",
    "ClassificationAccuracyEvaluator",
    "get_tokens",
]
