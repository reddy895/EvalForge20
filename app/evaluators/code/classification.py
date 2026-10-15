"""Classification accuracy and label matching evaluators for categorization tasks."""

import re

from app.domain.contracts import EvaluatorContract, EvaluatorInput
from app.domain.results import MetricResult
from app.evaluators.registry import MetricCategory, MetricDefinition, registry


def _clean_label(text: str) -> str:
    """Normalize label by stripping quotes, markdown formatting, and outer punctuation."""
    cleaned = text.strip().lower()
    # Remove markdown bold/italics
    cleaned = re.sub(r"[*_`]", "", cleaned)
    # Strip common leading conversational phrases (e.g. "The answer is: positive")
    prefix_match = re.search(
        r"(?:answer is|label is|class is|category is|classification:)\s*([a-zA-Z0-9_-]+)", cleaned
    )
    if prefix_match:
        return prefix_match.group(1).strip()
    # Remove outer punctuation
    cleaned = cleaned.strip("\"'.,;:")
    return cleaned


class ClassificationAccuracyEvaluator(EvaluatorContract):
    """Measures classification accuracy by verifying if the predicted class label matches reference."""

    @property
    def metric_id(self) -> str:
        return "classification_accuracy"

    @property
    def metric_name(self) -> str:
        return "Classification Accuracy"

    async def evaluate(self, eval_input: EvaluatorInput) -> MetricResult:
        if eval_input.case.expected_output is None:
            return MetricResult(
                metric_id=self.metric_id,
                metric_name=self.metric_name,
                score=None,
                passed=None,
                reason="Skipped: No reference classification label defined on case",
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

        pred_label = _clean_label(eval_input.actual_output)
        expected_label = _clean_label(eval_input.case.expected_output)

        # Direct match or containment check if output is verbose
        is_match = (pred_label == expected_label) or (expected_label in pred_label.split())
        score = 1.0 if is_match else 0.0

        return MetricResult(
            metric_id=self.metric_id,
            metric_name=self.metric_name,
            score=score,
            passed=is_match,
            reason=(
                f"Classification match: '{pred_label}' == '{expected_label}'"
                if is_match
                else f"Classification mismatch: got '{pred_label}', expected '{expected_label}'"
            ),
            details={
                "predicted_label": pred_label,
                "expected_label": expected_label,
                "category": eval_input.case.category,
            },
            is_model_based=False,
        )


registry.register(
    ClassificationAccuracyEvaluator,
    MetricDefinition(
        metric_id="classification_accuracy",
        metric_name="Classification Accuracy",
        description="Assesses whether the predicted class label matches the expected ground-truth category.",
        category=MetricCategory.DETERMINISTIC,
        requires_expected_output=True,
    ),
)
