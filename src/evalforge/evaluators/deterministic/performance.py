"""Latency, throughput, and performance efficiency evaluators."""

from typing import Any

from pydantic import BaseModel

from src.evalforge.evaluators.base import BaseEvaluator, MetricResult


class PerformanceMetrics(BaseModel):
    latency_ms: float
    throughput_tok_s: float | None = None
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    total_tokens: int | None = None
    meets_sla: bool = True


class LatencySlaEvaluator(BaseEvaluator):
    """Evaluates inference latency against a user-defined latency SLA target."""

    name = "latency_sla"
    version = "1.0.0"
    is_deterministic = True

    async def evaluate(
        self,
        prediction: str,
        reference: str | None = None,
        context: str | None = None,
        latency_ms: float = 0.0,
        max_latency_ms: float = 2000.0,
        completion_tokens: int | None = None,
        prompt_tokens: int | None = None,
        **kwargs: Any,
    ) -> MetricResult:
        passed = latency_ms <= max_latency_ms
        score = (
            1.0
            if passed
            else max(0.0, round(1.0 - ((latency_ms - max_latency_ms) / max_latency_ms), 2))
        )

        throughput_tok_s: float | None = None
        if completion_tokens is not None and latency_ms > 0:
            throughput_tok_s = round(completion_tokens / (latency_ms / 1000.0), 2)

        return MetricResult(
            name=self.name,
            score=score,
            passed=passed,
            method="latency_sla_check",
            details={
                "measured_latency_ms": latency_ms,
                "max_latency_ms": max_latency_ms,
                "throughput_tokens_per_sec": throughput_tok_s,
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
            },
        )
