"""Multi-run comparison engine for benchmarking two or more evaluation runs across models and prompts."""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.domain.results import CaseResult
from app.runner.config import EvaluationRunRecord


class RunSummaryHeader(BaseModel):
    """High-level metadata summary for a single run in the comparison matrix."""

    model_config = ConfigDict(frozen=True)

    run_id: str
    model_identifier: str
    provider: str
    dataset_name: str
    dataset_version_hash: str | None = None
    prompt_version: str | None = None
    total_cases: int = 0
    passed_cases: int = 0
    pass_rate: float = 0.0
    mean_latency_ms: float | None = None
    error_rate: float = 0.0
    status: str = "completed"


class MetricComparisonRow(BaseModel):
    """Comparison row for a specific metric across multiple runs."""

    model_config = ConfigDict(frozen=True)

    metric_id: str
    metric_name: str
    values: dict[str, float | None] = Field(default_factory=dict, description="run_id -> metric value")
    best_run_id: str | None = None
    worst_run_id: str | None = None
    spread: float | None = None


class CaseDisagreement(BaseModel):
    """Evaluation case where compared runs produced conflicting pass/fail results."""

    model_config = ConfigDict(frozen=True)

    case_id: str
    input_preview: str
    run_results: dict[str, bool | None] = Field(default_factory=dict, description="run_id -> passed")


class MultiRunComparisonMatrix(BaseModel):
    """Comprehensive comparison matrix across multiple evaluation runs."""

    model_config = ConfigDict(frozen=True)

    run_ids: list[str]
    runs: list[RunSummaryHeader]
    metric_rows: list[MetricComparisonRow]
    fastest_run_id: str | None = None
    highest_accuracy_run_id: str | None = None
    case_disagreements: list[CaseDisagreement] = Field(default_factory=list)
    dataset_consistent: bool = True
    summary: str = ""


def compare_multiple_runs(
    runs: list[EvaluationRunRecord],
    cases_by_run: dict[str, list[CaseResult]] | None = None,
) -> MultiRunComparisonMatrix:
    """Compare two or more evaluation runs across models, metrics, and case outcomes."""
    if not runs:
        raise ValueError("At least one evaluation run is required for comparison.")

    cases_by_run = cases_by_run or {}
    dataset_hashes = {r.config.dataset_version_hash for r in runs if r.config.dataset_version_hash}
    dataset_consistent = len(dataset_hashes) <= 1

    headers: list[RunSummaryHeader] = []
    for r in runs:
        total = r.metrics.total_cases if r.metrics else r.total_cases
        pass_rate = round(r.metrics.pass_rate, 4) if (r.metrics and r.metrics.pass_rate is not None) else 0.0
        passed = int(round(pass_rate * total))
        err_count = (
            sum(r.metrics.error_distribution.values())
            if (r.metrics and r.metrics.error_distribution)
            else r.failed_cases
        )
        err_rate = round(err_count / total, 4) if total > 0 else 0.0

        headers.append(
            RunSummaryHeader(
                run_id=r.run_id,
                model_identifier=r.config.model_identifier,
                provider=r.config.provider,
                dataset_name=r.config.dataset_name,
                dataset_version_hash=r.config.dataset_version_hash,
                prompt_version=r.config.options.get("prompt_version") if r.config.options else None,
                total_cases=total,
                passed_cases=passed,
                pass_rate=pass_rate,
                mean_latency_ms=r.metrics.mean_latency_ms if r.metrics else None,
                error_rate=err_rate,
                status=r.status.value if hasattr(r.status, "value") else str(r.status),
            )
        )

    # Collect all unique metric IDs evaluated across runs
    all_metrics: dict[str, str] = {}
    for r in runs:
        if r.metrics and r.metrics.metric_averages:
            for m_id in r.metrics.metric_averages:
                all_metrics[m_id] = m_id.replace("_", " ").title()

    metric_rows: list[MetricComparisonRow] = []
    for m_id, m_name in sorted(all_metrics.items()):
        values: dict[str, float | None] = {}
        valid_nums: list[tuple[str, float]] = []

        for r in runs:
            val = r.metrics.metric_averages.get(m_id) if r.metrics else None
            values[r.run_id] = val
            if val is not None:
                valid_nums.append((r.run_id, val))

        best_id: str | None = None
        worst_id: str | None = None
        spread: float | None = None

        if valid_nums:
            sorted_nums = sorted(valid_nums, key=lambda x: x[1])
            worst_id = sorted_nums[0][0]
            best_id = sorted_nums[-1][0]
            spread = round(sorted_nums[-1][1] - sorted_nums[0][1], 4)

        metric_rows.append(
            MetricComparisonRow(
                metric_id=m_id,
                metric_name=m_name,
                values=values,
                best_run_id=best_id,
                worst_run_id=worst_id,
                spread=spread,
            )
        )

    # Fastest and highest accuracy determination
    fastest_run_id = None
    latencies = [(h.run_id, h.mean_latency_ms) for h in headers if h.mean_latency_ms is not None]
    if latencies:
        fastest_run_id = min(latencies, key=lambda x: x[1])[0]

    highest_accuracy_run_id = None
    if headers:
        highest_accuracy_run_id = max(headers, key=lambda h: h.pass_rate).run_id

    # Per-case disagreement detection if case details provided
    disagreements: list[CaseDisagreement] = []
    if cases_by_run and len(runs) > 1:
        # Group cases by case_id across runs
        case_outcomes: dict[str, dict[str, Any]] = {}
        for r_id, cases in cases_by_run.items():
            for c in cases:
                if c.case_id not in case_outcomes:
                    case_outcomes[c.case_id] = {
                        "input_preview": str(c.actual_output or "")[:60],
                        "runs": {},
                    }
                case_outcomes[c.case_id]["runs"][r_id] = c.passed

        for c_id, data in sorted(case_outcomes.items()):
            pass_vals = {v for v in data["runs"].values() if v is not None}
            if len(pass_vals) > 1:  # Conflicting pass/fail outcomes between runs
                disagreements.append(
                    CaseDisagreement(
                        case_id=c_id,
                        input_preview=data["input_preview"],
                        run_results=data["runs"],
                    )
                )

    # Construct human-readable summary
    models_str = ", ".join(f"'{h.model_identifier}' ({h.run_id[:8]})" for h in headers)
    summary_parts = [f"Compared {len(runs)} evaluation runs across {models_str}."]
    if highest_accuracy_run_id:
        acc_h = next(h for h in headers if h.run_id == highest_accuracy_run_id)
        summary_parts.append(f"Highest pass rate: {acc_h.pass_rate * 100:.1f}% ({acc_h.model_identifier}).")
    if fastest_run_id:
        fast_h = next(h for h in headers if h.run_id == fastest_run_id)
        if fast_h.mean_latency_ms is not None:
            summary_parts.append(f"Fastest run: {fast_h.mean_latency_ms:.1f}ms ({fast_h.model_identifier}).")
    if disagreements:
        summary_parts.append(f"Disagreements detected on {len(disagreements)} individual cases.")

    return MultiRunComparisonMatrix(
        run_ids=[r.run_id for r in runs],
        runs=headers,
        metric_rows=metric_rows,
        fastest_run_id=fastest_run_id,
        highest_accuracy_run_id=highest_accuracy_run_id,
        case_disagreements=disagreements,
        dataset_consistent=dataset_consistent,
        summary=" ".join(summary_parts),
    )
