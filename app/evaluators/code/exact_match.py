"""Exact match evaluator."""

from app.domain.contracts import EvaluatorContract, EvaluatorInput
from app.domain.results import MetricResult
from app.evaluators.registry import MetricCategory, MetricDefinition, registry


class ExactMatchEvaluator(EvaluatorContract):
    """Evaluates whether actual output strictly equals expected output."""

    @property
    def metric_id(self) -> str:
        return "exact_match"

    @property
    def metric_name(self) -> str:
        return "Exact Match"

    async def evaluate(self, eval_input: EvaluatorInput) -> MetricResult:
        expected = eval_input.case.expected_output
        actual = eval_input.actual_output

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

        is_match = actual == expected
        return MetricResult(
            metric_id=self.metric_id,
            metric_name=self.metric_name,
            score=1.0 if is_match else 0.0,
            passed=is_match,
            reason="Output matches expected reference exactly"
            if is_match
            else "Output does not match reference",
            details={"actual": str(actual), "expected": str(expected)},
            is_model_based=False,
        )


registry.register(
    ExactMatchEvaluator,
    MetricDefinition(
        metric_id="exact_match",
        metric_name="Exact Match",
        description="Checks whether system output strictly equals the expected reference string or structure.",
        category=MetricCategory.DETERMINISTIC,
        requires_expected_output=True,
    ),
)
