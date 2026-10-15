"""Standardized JSON evaluation report exporter."""

import json
from pathlib import Path
from typing import Any

from app.domain.results import AggregateMetrics, CaseResult
from app.runner.config import EvaluationRunRecord

REPORT_SCHEMA_VERSION = "1.0.0"


def generate_json_report(
    record: EvaluationRunRecord,
    case_results: list[CaseResult],
    aggregates: AggregateMetrics,
    integration_refs: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Generate a documented, reproducible JSON report following EvalForge20 specification."""
    duration_s: float | None = None
    if record.started_at and record.completed_at:
        duration_s = round((record.completed_at - record.started_at).total_seconds(), 2)

    # Detect limitations and missing data
    limitations: list[str] = []
    cases_missing_tokens = sum(1 for c in case_results if not c.token_usage)
    if cases_missing_tokens > 0:
        limitations.append(
            f"Token counts unmeasured for {cases_missing_tokens}/{len(case_results)} cases; total_tokens reflects only reporting providers."
        )

    skipped_metrics = 0
    for c in case_results:
        for m in c.metrics:
            if m.score is None and m.passed is None:
                skipped_metrics += 1
    if skipped_metrics > 0:
        limitations.append(
            f"{skipped_metrics} metric evaluations were skipped due to missing reference outputs or schemas."
        )

    # Format per-case results
    cases_payload = []
    for c in case_results:
        cases_payload.append(
            {
                "case_id": c.case_id,
                "input": c.input,
                "actual_output": c.actual_output,
                "expected_output": c.expected_output,
                "latency_ms": c.latency_ms,
                "token_usage": c.token_usage,
                "error_category": c.error_category,
                "error_message": c.error_message,
                "metrics": [m.model_dump() for m in c.metrics],
            }
        )

    report: dict[str, Any] = {
        "report_schema_version": REPORT_SCHEMA_VERSION,
        "run_id": record.run_id,
        "run_name": record.name,
        "status": record.status.value,
        "dataset_identity": {
            "version_hash": record.config.dataset_version_hash,
            "total_cases": record.total_cases,
        },
        "target_configuration": record.config.target.model_dump(),
        "evaluator_configurations": [e.model_dump() for e in record.config.evaluators],
        "timing": {
            "started_at": record.started_at.isoformat() if record.started_at else None,
            "completed_at": record.completed_at.isoformat() if record.completed_at else None,
            "duration_seconds": duration_s,
        },
        "case_counts": {
            "total_cases": record.total_cases,
            "completed_cases": record.completed_cases,
            "failed_cases": record.failed_cases,
        },
        "aggregate_metrics": aggregates.model_dump(),
        "per_case_results": cases_payload,
        "integration_references": integration_refs or {},
        "limitations_and_missing_data": limitations,
    }

    return report


def export_report_to_file(path: Path | str, report_data: dict[str, Any]) -> Path:
    """Serialize JSON report to disk."""
    dest = Path(path)
    dest.parent.mkdir(parents=True, exist_ok=True)
    with dest.open("w", encoding="utf-8") as f:
        json.dump(report_data, f, indent=2, ensure_ascii=False)
    return dest
