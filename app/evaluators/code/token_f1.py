"""Token-level Precision, Recall, and F1 score evaluators for sequence evaluation."""

import re
from collections import Counter

from app.domain.contracts import EvaluatorContract, EvaluatorInput
from app.domain.results import MetricResult
from app.evaluators.registry import MetricCategory, MetricDefinition, registry


def _tokenize(text: str) -> list[str]:
    """Lowercase and extract alphanumeric token sequence."""
    return re.findall(r"\b\w+\b", text.lower())


class TokenF1Evaluator(EvaluatorContract):
    """Computes harmonic mean of token-level precision and recall between actual and expected output."""

    @property
    def metric_id(self) -> str:
        return "token_f1"

    @property
    def metric_name(self) -> str:
        return "Token-level F1 Score"

    async def evaluate(self, eval_input: EvaluatorInput) -> MetricResult:
        if eval_input.case.expected_output is None:
            return MetricResult(
                metric_id=self.metric_id,
                metric_name=self.metric_name,
                score=None,
                passed=None,
                reason="Skipped: No expected_output defined on case",
                is_model_based=False,
            )

        if not eval_input.actual_output or not eval_input.actual_output.strip():
            return MetricResult(
                metric_id=self.metric_id,
                metric_name=self.metric_name,
                score=0.0,
                passed=False,
                reason="Actual output is empty",
                is_model_based=False,
            )

        actual_tokens = _tokenize(eval_input.actual_output)
        expected_tokens = _tokenize(eval_input.case.expected_output)

        if not actual_tokens or not expected_tokens:
            score = 1.0 if actual_tokens == expected_tokens else 0.0
            return MetricResult(
                metric_id=self.metric_id,
                metric_name=self.metric_name,
                score=score,
                passed=score >= 0.5,
                reason=f"Empty token sets (match={actual_tokens == expected_tokens})",
                is_model_based=False,
            )

        common = Counter(actual_tokens) & Counter(expected_tokens)
        num_same = sum(common.values())

        if num_same == 0:
            return MetricResult(
                metric_id=self.metric_id,
                metric_name=self.metric_name,
                score=0.0,
                passed=False,
                reason="No common tokens between actual and expected output",
                details={
                    "actual_len": len(actual_tokens),
                    "expected_len": len(expected_tokens),
                    "overlap": 0,
                },
                is_model_based=False,
            )

        precision = num_same / len(actual_tokens)
        recall = num_same / len(expected_tokens)
        f1 = round((2 * precision * recall) / (precision + recall), 4)

        threshold = float(eval_input.options.get("threshold", 0.5))
        passed = f1 >= threshold

        return MetricResult(
            metric_id=self.metric_id,
            metric_name=self.metric_name,
            score=f1,
            passed=passed,
            reason=f"Token F1: {f1:.4f} (P={precision:.2%}, R={recall:.2%})",
            details={
                "precision": round(precision, 4),
                "recall": round(recall, 4),
                "f1": f1,
                "overlap_tokens": num_same,
                "actual_tokens_count": len(actual_tokens),
                "expected_tokens_count": len(expected_tokens),
                "threshold": threshold,
            },
            is_model_based=False,
        )


registry.register(
    TokenF1Evaluator,
    MetricDefinition(
        metric_id="token_f1",
        metric_name="Token-level F1 Score",
        description="Measures token-level word overlap harmonic mean (F1) against reference output.",
        category=MetricCategory.DETERMINISTIC,
        requires_expected_output=True,
    ),
)
