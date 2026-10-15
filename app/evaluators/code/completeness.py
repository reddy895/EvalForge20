"""Response completeness, sentence termination, and length bound evaluators."""

from app.domain.contracts import EvaluatorContract, EvaluatorInput
from app.domain.results import MetricResult
from app.evaluators.registry import MetricCategory, MetricDefinition, registry


class ResponseCompletenessEvaluator(EvaluatorContract):
    """Evaluates whether model generation is complete, non-empty, and terminates cleanly."""

    @property
    def metric_id(self) -> str:
        return "response_completeness"

    @property
    def metric_name(self) -> str:
        return "Response Completeness"

    async def evaluate(self, eval_input: EvaluatorInput) -> MetricResult:
        text = (eval_input.actual_output or "").strip()
        if not text:
            return MetricResult(
                metric_id=self.metric_id,
                metric_name=self.metric_name,
                score=0.0,
                passed=False,
                reason="Response is completely empty",
                is_model_based=False,
            )

        min_words = int(eval_input.options.get("min_words", 2))
        max_words = eval_input.options.get("max_words")
        words = text.split()
        word_count = len(words)

        if word_count < min_words:
            return MetricResult(
                metric_id=self.metric_id,
                metric_name=self.metric_name,
                score=round(word_count / min_words, 2),
                passed=False,
                reason=f"Response too brief ({word_count} words < required {min_words})",
                details={"word_count": word_count, "min_words": min_words},
                is_model_based=False,
            )

        if max_words and word_count > int(max_words):
            return MetricResult(
                metric_id=self.metric_id,
                metric_name=self.metric_name,
                score=0.5,
                passed=False,
                reason=f"Response exceeded max words ({word_count} > {max_words})",
                details={"word_count": word_count, "max_words": max_words},
                is_model_based=False,
            )

        # Check sentence termination or valid closing symbols
        valid_closers = (".", "!", "?", '"', "'", "}", "]", ")", "`")
        is_terminated = text.endswith(valid_closers)

        # Truncation check
        score = 1.0 if is_terminated else 0.7
        passed = is_terminated or (word_count >= min_words)

        return MetricResult(
            metric_id=self.metric_id,
            metric_name=self.metric_name,
            score=score,
            passed=passed,
            reason="Response is complete and properly terminated"
            if is_terminated
            else "Response appears potentially truncated (no closing sentence punctuation)",
            details={"word_count": word_count, "is_terminated": is_terminated},
            is_model_based=False,
        )


registry.register(
    ResponseCompletenessEvaluator,
    MetricDefinition(
        metric_id="response_completeness",
        metric_name="Response Completeness",
        description="Checks whether model generation is non-empty, meets word count bounds, and terminates properly.",
        category=MetricCategory.DETERMINISTIC,
        requires_expected_output=False,
    ),
)
