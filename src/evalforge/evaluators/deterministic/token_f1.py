"""Token-level Precision, Recall, and F1 Score metric evaluator."""

from collections import Counter
import re
import string
from typing import Any, List, Optional

from src.evalforge.evaluators.base import BaseEvaluator, MetricResult


class TokenF1Evaluator(BaseEvaluator):
    """Computes token-overlap Precision, Recall, and F1 score against a reference target."""

    name = "token_f1"
    version = "1.0.0"
    is_deterministic = True

    @staticmethod
    def tokenize(text: str) -> List[str]:
        """Normalize and tokenize text into token sequences."""
        clean = text.lower()
        clean = "".join(ch for ch in clean if ch not in set(string.punctuation))
        tokens = re.findall(r"\w+", clean)
        return tokens

    async def evaluate(
        self,
        prediction: str,
        reference: Optional[str] = None,
        context: Optional[str] = None,
        threshold: float = 0.7,
        **kwargs: Any,
    ) -> MetricResult:
        if reference is None:
            return MetricResult(
                name=self.name,
                score=0.0,
                passed=False,
                method="token_overlap_f1",
                details={"reason": "No reference output provided for token F1 calculation."},
            )

        pred_tokens = self.tokenize(prediction)
        ref_tokens = self.tokenize(reference)

        if not pred_tokens or not ref_tokens:
            is_both_empty = not pred_tokens and not ref_tokens
            score = 1.0 if is_both_empty else 0.0
            return MetricResult(
                name=self.name,
                score=score,
                passed=score >= threshold,
                method="token_overlap_f1",
                details={"precision": score, "recall": score, "f1": score},
            )

        common = Counter(pred_tokens) & Counter(ref_tokens)
        num_same = sum(common.values())

        if num_same == 0:
            return MetricResult(
                name=self.name,
                score=0.0,
                passed=False,
                method="token_overlap_f1",
                details={"precision": 0.0, "recall": 0.0, "f1": 0.0},
            )

        precision = 1.0 * num_same / len(pred_tokens)
        recall = 1.0 * num_same / len(ref_tokens)
        f1 = (2 * precision * recall) / (precision + recall)

        f1_score = round(f1, 4)
        passed = f1_score >= threshold

        return MetricResult(
            name=self.name,
            score=f1_score,
            passed=passed,
            method="token_overlap_f1",
            details={
                "precision": round(precision, 4),
                "recall": round(recall, 4),
                "f1": f1_score,
                "shared_token_count": num_same,
                "pred_token_count": len(pred_tokens),
                "ref_token_count": len(ref_tokens),
                "threshold": threshold,
            },
        )
