"""Run comparison engine validating compatibility, computing metric deltas, and enforcing regression thresholds."""

from pydantic import BaseModel, ConfigDict, Field

from app.domain.errors import ComparisonIncompatibleError
from app.domain.results import AggregateMetrics, CaseResult
from app.pricing.calculator import cost_calculator
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


class RegressionThresholds(BaseModel):
    """Configurable thresholds determining whether run changes constitute a regression."""

    model_config = ConfigDict(frozen=True)

    max_allowed_pass_rate_drop: float = Field(
        default=0.05,
        ge=0.0,
        le=1.0,
        description="Max acceptable drop in pass rate (e.g. 0.05 = 5%)",
    )
    max_allowed_latency_increase_ms: float | None = Field(
        default=250.0, ge=0.0, description="Max acceptable increase in mean latency in ms"
    )
    max_allowed_regressed_cases: int = Field(
        default=0,
        ge=0,
        description="Maximum number of individual cases allowed to flip from pass to fail",
    )


class ComparisonResult(BaseModel):
    """Complete structured comparison between two evaluation runs."""

    model_config = ConfigDict(frozen=True)

    baseline_run_id: str
    candidate_run_id: str
    baseline_model: str | None = None
    candidate_model: str | None = None
    is_compatible: bool
    dataset_version_hash: str | None
    metric_deltas: dict[str, MetricDelta] = Field(default_factory=dict)
    pass_rate_delta: float | None = None
    mean_latency_delta_ms: float | None = None
    median_latency_delta_ms: float | None = None
    p95_latency_delta_ms: float | None = None
    cost_delta_usd: float | None = None
    regressed_cases: list[CaseRegression] = Field(default_factory=list)
    improved_cases: list[CaseRegression] = Field(default_factory=list)
    regressions_detected: bool = False
    threshold_violations: list[str] = Field(default_factory=list)
    passed_regression_gate: bool = True
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


def calculate_metric_delta(
    base_val: float | None, cand_val: float | None
) -> tuple[float | None, float | None]:
    """Calculate absolute delta and percentage change."""
    if base_val is None or cand_val is None:
        return None, None
    delta = round(cand_val - base_val, 4)
    pct = round(((cand_val - base_val) / base_val) * 100.0, 2) if base_val != 0 else None
    return delta, pct


def evaluate_regression_thresholds(
    pass_rate_delta: float | None,
    latency_delta_ms: float | None,
    regressed_cases_count: int,
    thresholds: RegressionThresholds,
) -> tuple[bool, list[str]]:
    """Check comparison results against configured quality gate thresholds."""
    violations: list[str] = []

    # Check pass rate drop
    if pass_rate_delta is not None and pass_rate_delta < -thresholds.max_allowed_pass_rate_drop:
        violations.append(
            f"Pass rate dropped by {abs(pass_rate_delta):.2%}, exceeding allowed threshold of {thresholds.max_allowed_pass_rate_drop:.2%}"
        )

    # Check latency increase
    if (
        thresholds.max_allowed_latency_increase_ms is not None
        and latency_delta_ms is not None
        and latency_delta_ms > thresholds.max_allowed_latency_increase_ms
    ):
        violations.append(
            f"Mean latency increased by {latency_delta_ms:.1f}ms, exceeding allowed threshold of {thresholds.max_allowed_latency_increase_ms:.1f}ms"
        )

    # Check case flip regressions
    if regressed_cases_count > thresholds.max_allowed_regressed_cases:
        violations.append(
            f"{regressed_cases_count} individual cases regressed from pass to fail, exceeding allowed limit of {thresholds.max_allowed_regressed_cases}"
        )

    passed_gate = len(violations) == 0
    return passed_gate, violations


def compare_evaluation_runs(
    baseline: EvaluationRunRecord,
    baseline_cases: list[CaseResult],
    baseline_aggs: AggregateMetrics,
    candidate: EvaluationRunRecord,
    candidate_cases: list[CaseResult],
    candidate_aggs: AggregateMetrics,
    thresholds: RegressionThresholds | None = None,
    allow_different_datasets: bool = False,
) -> ComparisonResult:
    """Compare candidate run against baseline run, calculate deltas, and evaluate regression thresholds."""
    validate_run_compatibility(
        baseline, candidate, allow_different_datasets=allow_different_datasets
    )

    # 1. Metric deltas
    deltas: dict[str, MetricDelta] = {}
    all_metrics = set(baseline_aggs.metric_averages.keys()) | set(
        candidate_aggs.metric_averages.keys()
    )

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

    # Latency deltas
    lat_delta, _ = calculate_metric_delta(
        baseline_aggs.mean_latency_ms, candidate_aggs.mean_latency_ms
    )
    median_lat_delta, _ = calculate_metric_delta(
        baseline_aggs.median_latency_ms, candidate_aggs.median_latency_ms
    )
    p95_lat_delta, _ = calculate_metric_delta(
        baseline_aggs.p95_latency_ms, candidate_aggs.p95_latency_ms
    )

    # Cost deltas
    cost_delta = None
    try:
        base_cost = cost_calculator.calculate_run_cost(
            results=baseline_cases,
            aggregates=baseline_aggs,
            provider=baseline.config.provider,
            model_identifier=baseline.config.model_identifier,
        )
        cand_cost = cost_calculator.calculate_run_cost(
            results=candidate_cases,
            aggregates=candidate_aggs,
            provider=candidate.config.provider,
            model_identifier=candidate.config.model_identifier,
        )
        if (
            base_cost.total_estimated_cost_usd is not None
            and cand_cost.total_estimated_cost_usd is not None
        ):
            cost_delta = round(
                cand_cost.total_estimated_cost_usd - base_cost.total_estimated_cost_usd, 6
            )
    except Exception:
        pass

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

    # 3. Check quality gate thresholds
    active_thresholds = thresholds or RegressionThresholds()
    passed_gate, violations = evaluate_regression_thresholds(
        pass_rate_delta=pr_delta,
        latency_delta_ms=lat_delta,
        regressed_cases_count=len(regressed),
        thresholds=active_thresholds,
    )

    summary = (
        f"Compared candidate '{candidate.name}' ({candidate.run_id}) vs baseline '{baseline.name}' ({baseline.run_id}): "
        f"Pass rate delta: {pr_delta:+.2%} | Regressed cases: {len(regressed)} | Improved cases: {len(improved)} | "
        f"Gate Status: {'PASSED' if passed_gate else 'FAILED'}"
        if pr_delta is not None
        else "Comparison computed."
    )

    return ComparisonResult(
        baseline_run_id=baseline.run_id,
        candidate_run_id=candidate.run_id,
        baseline_model=baseline.config.model_identifier,
        candidate_model=candidate.config.model_identifier,
        is_compatible=True,
        dataset_version_hash=candidate.config.dataset_version_hash,
        metric_deltas=deltas,
        pass_rate_delta=pr_delta,
        mean_latency_delta_ms=lat_delta,
        median_latency_delta_ms=median_lat_delta,
        p95_latency_delta_ms=p95_lat_delta,
        cost_delta_usd=cost_delta,
        regressed_cases=regressed,
        improved_cases=improved,
        regressions_detected=len(regressed) > 0,
        threshold_violations=violations,
        passed_regression_gate=passed_gate,
        summary=summary,
    )
