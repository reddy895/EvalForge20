"""Contains match evaluator verifying presence of reference substring or phrases."""

from app.domain.contracts import EvaluatorContract, EvaluatorInput
from app.domain.results import MetricResult
from app.evaluators.registry import MetricCategory, MetricDefinition, registry


class ContainsMatchEvaluator(EvaluatorContract):
    """Evaluates whether the actual output contains the expected reference substring."""

    @property
    def metric_id(self) -> str:
        return "contains_match"

    @property
    def metric_name(self) -> str:
        return "Contains Match"

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

        if not actual:
            return MetricResult(
                metric_id=self.metric_id,
                metric_name=self.metric_name,
                score=0.0,
                passed=False,
                reason="Actual output is empty",
                details={"actual": "", "expected": str(expected)},
                is_model_based=False,
            )

        case_sensitive = bool(eval_input.options.get("case_sensitive", False))
        act_text = str(actual) if case_sensitive else str(actual).lower()
        exp_text = str(expected) if case_sensitive else str(expected).lower()

        # Check containment
        is_contained = exp_text in act_text
        score = 1.0 if is_contained else 0.0

        return MetricResult(
            metric_id=self.metric_id,
            metric_name=self.metric_name,
            score=score,
            passed=is_contained,
            reason="Output contains the expected reference text"
            if is_contained
            else "Output does not contain the expected reference text",
            details={
                "actual_snippet": str(actual)[:200],
                "expected": str(expected),
                "case_sensitive": case_sensitive,
            },
            is_model_based=False,
        )


registry.register(
    ContainsMatchEvaluator,
    MetricDefinition(
        metric_id="contains_match",
        metric_name="Contains Match",
        description="Verifies that the generated model response contains the target ground-truth reference string.",
        category=MetricCategory.DETERMINISTIC,
        requires_expected_output=True,
    ),
)
