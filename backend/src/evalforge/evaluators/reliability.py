"""Reliability, failure rate, timeout, and response integrity evaluators."""

from typing import Any

from src.evalforge.evaluators.base import BaseEvaluator, MetricResult


class ReliabilityEvaluator(BaseEvaluator):
    """Evaluates whether an inference response completed reliably without timeouts or empty output."""

    evaluator_id: str = "reliability"
    name: str = "reliability"
    version: str = "1.0.0"
    is_deterministic: bool = True
    required_inputs: list[str] = ["prediction"]

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(
            name="reliability",
            evaluator_id="reliability",
            description="Evaluates inference request success, non-empty response integrity, and error absence.",
            **kwargs,
        )

    async def evaluate(
        self,
        prediction: str,
        reference: str | None = None,
        context: str | None = None,
        error_message: str | None = None,
        is_timeout: bool = False,
        **kwargs: Any,
    ) -> MetricResult:
        has_error = bool(error_message)
        is_empty = not str(prediction).strip()

        passed = not has_error and not is_timeout and not is_empty
        score = 1.0 if passed else 0.0

        failure_reason = None
        if is_timeout:
            failure_reason = "timeout"
        elif has_error:
            failure_reason = error_message
        elif is_empty:
            failure_reason = "empty_response"

        return MetricResult(
            name=self.name,
            score=score,
            passed=passed,
            method="response_integrity_audit",
            details={
                "is_timeout": is_timeout,
                "has_error": has_error,
                "is_empty": is_empty,
                "failure_reason": failure_reason,
            },
        )

    def aggregate(self, results: list[MetricResult]) -> dict[str, Any]:
        """Compute success rate, failure rate, timeout rate, and invalid response rate."""
        total = len(results)
        if total == 0:
            return {
                "count": 0,
                "success_rate": 0.0,
                "failure_rate": 0.0,
                "timeout_rate": 0.0,
                "invalid_response_rate": 0.0,
            }

        successful = sum(1 for r in results if r.passed)
        timeouts = sum(1 for r in results if r.details.get("is_timeout"))
        empty_or_invalid = sum(1 for r in results if r.details.get("is_empty"))
        failed = total - successful

        return {
            "count": total,
            "success_rate": round(successful / total, 4),
            "failure_rate": round(failed / total, 4),
            "timeout_rate": round(timeouts / total, 4),
            "invalid_response_rate": round(empty_or_invalid / total, 4),
            "successful_requests": successful,
            "failed_requests": failed,
        }


__all__ = ["ReliabilityEvaluator"]
