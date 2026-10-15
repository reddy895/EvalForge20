"""Run comparison engine validating compatibility and computing metric deltas."""

from pydantic import BaseModel, ConfigDict, Field

from app.domain.errors import ComparisonIncompatibleError
from app.domain.results import AggregateMetrics, CaseResult
from app.runner.config import EvaluationRunRecord


class MetricDelta(BaseModel):
    """Quantitative delta between baseline and candidate for a specific metric."""

    model_config = ConfigDict(frozen=True)

    metric_id: str
    baseline_value: float | None
    candidate_value: float | None
    delta: float | None
    percentage_change: float | None


class CaseRegression(BaseModel):
    """Per-case performance flip between baseline and candidate."""

    model_config = ConfigDict(frozen=True)

    case_id: str
    baseline_passed: bool | None
    candidate_passed: bool | None
    reason: str


class ComparisonResult(BaseModel):
    """Complete structured comparison between two evaluation runs."""

    model_config = ConfigDict(frozen=True)

    baseline_run_id: str
    candidate_run_id: str
    is_compatible: bool
    dataset_version_hash: str | None
    metric_deltas: dict[str, MetricDelta] = Field(default_factory=dict)
    pass_rate_delta: float | None = None
    mean_latency_delta_ms: float | None = None
    regressed_cases: list[CaseRegression] = Field(default_factory=list)
    improved_cases: list[CaseRegression] = Field(default_factory=list)
    regressions_detected: bool = False
    summary: str = ""


def validate_run_compatibility(
    baseline: EvaluationRunRecord,
    candidate: EvaluationRunRecord,
    allow_different_datasets: bool = False,
) -> None:
    """Ensure runs evaluated the exact same dataset version before comparing."""
    base_hash = baseline.config.dataset_version_hash
    cand_hash = candidate.config.dataset_version_hash

    if not allow_different_datasets and base_hash and cand_hash and base_hash != cand_hash:
        raise ComparisonIncompatibleError(
            f"Runs are incompatible: baseline dataset hash ({base_hash[:8]}...) != "
            f"candidate dataset hash ({cand_hash[:8]}...)."
        )


def calculate_metric_delta(base_val: float | None, cand_val: float | None) -> tuple[float | None, float | None]:
    """Calculate absolute delta and percentage change."""
    if base_val is None or cand_val is None:
        return None, None
    delta = round(cand_val - base_val, 4)
    pct = round(((cand_val - base_val) / base_val) * 100.0, 2) if base_val != 0 else None
    return delta, pct


def compare_evaluation_runs(
    baseline: EvaluationRunRecord,
    baseline_cases: list[CaseResult],
    baseline_aggs: AggregateMetrics,
    candidate: EvaluationRunRecord,
    candidate_cases: list[CaseResult],
    candidate_aggs: AggregateMetrics,
    allow_different_datasets: bool = False,
) -> ComparisonResult:
    """Compare candidate run against baseline run and compute metric deltas."""
    validate_run_compatibility(baseline, candidate, allow_different_datasets=allow_different_datasets)

    # 1. Metric deltas
    deltas: dict[str, MetricDelta] = {}
    all_metrics = set(baseline_aggs.metric_averages.keys()) | set(candidate_aggs.metric_averages.keys())

    for mid in sorted(all_metrics):
        bv = baseline_aggs.metric_averages.get(mid)
        cv = candidate_aggs.metric_averages.get(mid)
        d, pct = calculate_metric_delta(bv, cv)
        deltas[mid] = MetricDelta(
            metric_id=mid,
            baseline_value=bv,
            candidate_value=cv,
            delta=d,
            percentage_change=pct,
        )

    # Pass rate delta
    pr_delta, _ = calculate_metric_delta(baseline_aggs.pass_rate, candidate_aggs.pass_rate)

    # Latency delta
    lat_delta, _ = calculate_metric_delta(baseline_aggs.mean_latency_ms, candidate_aggs.mean_latency_ms)

    # 2. Case flips
    base_case_map = {c.case_id: c for c in baseline_cases}
    regressed: list[CaseRegression] = []
    improved: list[CaseRegression] = []

    for cand_case in candidate_cases:
        base_case = base_case_map.get(cand_case.case_id)
        if not base_case:
            continue

        base_passed = (
            all(m.passed for m in base_case.metrics if m.passed is not None)
            if base_case.metrics
            else None
        )
        cand_passed = (
            all(m.passed for m in cand_case.metrics if m.passed is not None)
            if cand_case.metrics
            else None
        )

        if base_passed is True and cand_passed is False:
            regressed.append(
                CaseRegression(
                    case_id=cand_case.case_id,
                    baseline_passed=True,
                    candidate_passed=False,
                    reason=f"Passed in baseline but failed in candidate ({cand_case.error_category or 'failed metrics'})",
                )
            )
        elif base_passed is False and cand_passed is True:
            improved.append(
                CaseRegression(
                    case_id=cand_case.case_id,
                    baseline_passed=False,
                    candidate_passed=True,
                    reason="Failed in baseline but passed in candidate",
                )
            )

    summary = (
        f"Compared candidate '{candidate.name}' ({candidate.run_id}) vs baseline '{baseline.name}' ({baseline.run_id}): "
        f"Pass rate delta: {pr_delta:+.2%} | Regressed cases: {len(regressed)} | Improved cases: {len(improved)}"
        if pr_delta is not None
        else "Comparison computed."
    )

    return ComparisonResult(
        baseline_run_id=baseline.run_id,
        candidate_run_id=candidate.run_id,
        is_compatible=True,
        dataset_version_hash=candidate.config.dataset_version_hash,
        metric_deltas=deltas,
        pass_rate_delta=pr_delta,
        mean_latency_delta_ms=lat_delta,
        regressed_cases=regressed,
        improved_cases=improved,
        regressions_detected=len(regressed) > 0,
        summary=summary,
    )
