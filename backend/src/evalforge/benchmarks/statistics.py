"""Statistical aggregation and comparative metric matrix calculation."""

from src.evalforge.evaluators.aggregator import aggregate_scorecard
from src.evalforge.schemas.benchmark import ModelComparisonMetrics
from src.evalforge.storage.models.evaluation import CaseResult


def compute_model_metrics(
    model_id: str,
    provider: str,
    evaluation_id: str,
    results: list[CaseResult],
) -> ModelComparisonMetrics:
    """Aggregate individual case results into verified comparison metrics without fabricated values."""
    scorecard = aggregate_scorecard(results)

    tot_tokens: int | None = None
    if scorecard.total_prompt_tokens is not None or scorecard.total_completion_tokens is not None:
        tot_tokens = (scorecard.total_prompt_tokens or 0) + (scorecard.total_completion_tokens or 0)

    return ModelComparisonMetrics(
        model_id=model_id,
        provider=provider,
        evaluation_id=evaluation_id,
        pass_rate=scorecard.pass_rate,
        passed_cases=scorecard.passed_cases,
        failed_cases=scorecard.failed_cases,
        total_cases=scorecard.total_cases,
        avg_latency_ms=scorecard.avg_latency_ms,
        p50_latency_ms=scorecard.p50_latency_ms,
        p95_latency_ms=scorecard.p95_latency_ms,
        avg_throughput_tok_s=scorecard.avg_throughput_tok_s,
        total_tokens=tot_tokens,
        metric_breakdown=scorecard.metric_averages,
    )
