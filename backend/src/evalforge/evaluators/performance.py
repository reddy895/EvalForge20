"""Performance, latency, throughput, and token-rate evaluators."""

import statistics
from typing import Any

from src.evalforge.evaluators.base import BaseEvaluator, MetricResult


class LatencyEvaluator(BaseEvaluator):
    """Evaluates request latency against threshold SLA and calculates response time metrics."""

    evaluator_id: str = "latency"
    name: str = "latency"
    version: str = "1.0.0"
    is_deterministic: bool = True
    required_inputs: list[str] = ["prediction"]

    def __init__(self, max_latency_ms: float = 2000.0, **kwargs: Any) -> None:
        super().__init__(
            name="latency",
            evaluator_id="latency",
            description="Measures inference request latency in milliseconds against SLA targets.",
            **kwargs,
        )
        self.max_latency_ms = max_latency_ms

    async def evaluate(
        self,
        prediction: str,
        reference: str | None = None,
        context: str | None = None,
        latency_ms: float = 0.0,
        **kwargs: Any,
    ) -> MetricResult:
        passed = latency_ms <= self.max_latency_ms
        score = 1.0 if passed else max(0.0, round(1.0 - ((latency_ms - self.max_latency_ms) / self.max_latency_ms), 3))

        return MetricResult(
            name=self.name,
            score=score,
            passed=passed,
            method="latency_sla_measurement",
            details={
                "measured_latency_ms": round(latency_ms, 2),
                "target_max_latency_ms": self.max_latency_ms,
                "passed_sla": passed,
            },
        )

    def aggregate(self, results: list[MetricResult]) -> dict[str, Any]:
        """Compute average, median, and P95 latency across evaluated requests."""
        if not results:
            return {
                "count": 0,
                "average_latency_ms": 0.0,
                "median_latency_ms": 0.0,
                "p95_latency_ms": 0.0,
                "min_latency_ms": 0.0,
                "max_latency_ms": 0.0,
            }

        latencies = [
            r.details.get("measured_latency_ms", 0.0)
            for r in results
            if "measured_latency_ms" in r.details
        ]
        if not latencies:
            return super().aggregate(results)

        latencies.sort()
        avg_lat = sum(latencies) / len(latencies)
        med_lat = statistics.median(latencies)
        p95_idx = int(len(latencies) * 0.95)
        p95_lat = latencies[min(p95_idx, len(latencies) - 1)]

        return {
            "count": len(results),
            "average_latency_ms": round(avg_lat, 2),
            "median_latency_ms": round(med_lat, 2),
            "p95_latency_ms": round(p95_lat, 2),
            "min_latency_ms": round(latencies[0], 2),
            "max_latency_ms": round(latencies[-1], 2),
            "sla_pass_rate": round(sum(1 for r in results if r.passed) / len(results), 4),
        }


class TokensPerSecondEvaluator(BaseEvaluator):
    """Calculates generation throughput in tokens per second."""

    evaluator_id: str = "tokens_per_second"
    name: str = "tokens_per_second"
    version: str = "1.0.0"
    is_deterministic: bool = True
    required_inputs: list[str] = ["prediction"]

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(
            name="tokens_per_second",
            evaluator_id="tokens_per_second",
            description="Measures generation speed: output tokens divided by duration in seconds.",
            **kwargs,
        )

    async def evaluate(
        self,
        prediction: str,
        reference: str | None = None,
        context: str | None = None,
        latency_ms: float = 0.0,
        completion_tokens: int | None = None,
        **kwargs: Any,
    ) -> MetricResult:
        tokens = completion_tokens
        if tokens is None:
            # Fallback approximate token count: words * 1.3
            tokens = max(1, int(len(str(prediction).split()) * 1.3))

        tok_sec = round(tokens / (latency_ms / 1000.0), 2) if latency_ms > 0 else 0.0

        return MetricResult(
            name=self.name,
            score=tok_sec,
            passed=tok_sec > 0.0,
            method="tokens_per_second_calculation",
            details={
                "tokens": tokens,
                "duration_seconds": round(latency_ms / 1000.0, 3) if latency_ms > 0 else 0.0,
                "tokens_per_second": tok_sec,
            },
        )


__all__ = [
    "LatencyEvaluator",
    "TokensPerSecondEvaluator",
]
