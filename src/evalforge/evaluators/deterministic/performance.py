"""Latency, throughput, and performance efficiency evaluators."""

from typing import Any, Dict, Optional
from pydantic import BaseModel

from src.evalforge.evaluators.base import BaseEvaluator, MetricResult


class PerformanceMetrics(BaseModel):
    latency_ms: float
    throughput_tok_s: Optional[float] = None
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    total_tokens: Optional[int] = None
    meets_sla: bool = True


class LatencySlaEvaluator(BaseEvaluator):
    """Evaluates inference latency against a user-defined latency SLA target."""

    name = "latency_sla"
    version = "1.0.0"
    is_deterministic = True

    async def evaluate(
        self,
        prediction: str,
        reference: Optional[str] = None,
        context: Optional[str] = None,
        latency_ms: float = 0.0,
        max_latency_ms: float = 2000.0,
        completion_tokens: Optional[int] = None,
        prompt_tokens: Optional[int] = None,
        **kwargs: Any,
    ) -> MetricResult:
        passed = latency_ms <= max_latency_ms
        score = 1.0 if passed else max(0.0, round(1.0 - ((latency_ms - max_latency_ms) / max_latency_ms), 2))

        throughput_tok_s: Optional[float] = None
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
