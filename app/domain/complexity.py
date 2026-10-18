"""Complexity bands and task capability analysis domain definitions."""

import statistics
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.domain.models import EvaluationCase
from app.domain.results import CaseResult


class ComplexityBand(StrEnum):
    """Complexity tiers for benchmark categorization."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    UNKNOWN = "unknown"


class BandMetrics(BaseModel):
    """Aggregate measurements for a single complexity band."""

    model_config = ConfigDict(frozen=True)

    band: ComplexityBand
    total_cases: int = Field(default=0, ge=0)
    passed_cases: int = Field(default=0, ge=0)
    pass_rate: float | None = Field(default=None, ge=0.0, le=1.0)
    mean_latency_ms: float | None = Field(default=None, ge=0.0)
    has_sufficient_data: bool = Field(
        default=False,
        description="True if total_cases >= 3; bands with < 3 cases show insufficient data indicator",
    )
    insufficient_data_note: str | None = Field(
        default=None, description="Explanation when sample size is below threshold"
    )


class TaskCategoryMetrics(BaseModel):
    """Performance breakdown for a task capability category."""

    model_config = ConfigDict(frozen=True)

    category: str
    total_cases: int = Field(default=0, ge=0)
    passed_cases: int = Field(default=0, ge=0)
    failed_cases: int = Field(default=0, ge=0)
    pass_rate: float | None = Field(default=None, ge=0.0, le=1.0)
    failure_rate: float | None = Field(default=None, ge=0.0, le=1.0)
    mean_latency_ms: float | None = Field(default=None, ge=0.0)
    representative_failures: list[dict[str, Any]] = Field(default_factory=list)


def classify_case_complexity(case: EvaluationCase) -> ComplexityBand:
    """Determine complexity tier from explicit metadata or deterministic heuristic.

    - Explicit metadata: 'complexity' or 'difficulty' (low, medium, high).
    - High: Tool use, RAG multi-context (> 1 context), long prompts (> 1500 chars), or JSON schemas.
    - Medium: Multi-assertion checks, medium length (> 300 chars), or multiple constraints.
    - Low: Direct question answering, short queries, simple classification.
    """
    explicit = (
        case.metadata.get("complexity")
        or case.metadata.get("difficulty")
        or case.metadata.get("tier")
    )
    if explicit:
        val = str(explicit).lower().strip()
        if val in ("low", "easy", "simple"):
            return ComplexityBand.LOW
        elif val in ("medium", "med", "moderate"):
            return ComplexityBand.MEDIUM
        elif val in ("high", "hard", "complex"):
            return ComplexityBand.HIGH

    # Deterministic heuristics
    if case.tools or (case.context and len(case.context) > 1) or case.metadata.get("schema"):
        return ComplexityBand.HIGH

    text_len = len(str(case.input))
    if text_len > 1500:
        return ComplexityBand.HIGH
    elif text_len > 300 or case.metadata.get("assertions"):
        return ComplexityBand.MEDIUM

    return ComplexityBand.LOW


def aggregate_complexity_bands(
    case_results: list[CaseResult],
    cases_map: dict[str, EvaluationCase] | None = None,
) -> dict[str, BandMetrics]:
    """Group results by complexity band and calculate metrics with < 3 insufficient data threshold."""
    cases_map = cases_map or {}
    band_cases: dict[ComplexityBand, list[tuple[CaseResult, bool]]] = {
        ComplexityBand.LOW: [],
        ComplexityBand.MEDIUM: [],
        ComplexityBand.HIGH: [],
    }

    for res in case_results:
        case = cases_map.get(res.case_id)
        if case:
            band = classify_case_complexity(case)
        else:
            # Fallback if case metadata was stored on trace
            tier = (res.trace or {}).get("complexity") if res.trace else None
            if tier == "high":
                band = ComplexityBand.HIGH
            elif tier == "medium":
                band = ComplexityBand.MEDIUM
            else:
                band = ComplexityBand.LOW

        if band not in band_cases:
            band_cases[band] = []
        band_cases[band].append((res, res.passed))

    output: dict[str, BandMetrics] = {}
    for band_key, items in band_cases.items():
        total = len(items)
        passed = sum(1 for _, p in items if p)
        latencies = [
            r.latency_ms for r, _ in items if r.latency_ms is not None and r.latency_ms > 0
        ]
        mean_lat = round(statistics.fmean(latencies), 2) if latencies else None

        # Threshold: At least 3 cases required for statistical significance
        has_sufficient = total >= 3
        pass_rate = round(passed / total, 4) if total > 0 else None
        note = (
            None
            if has_sufficient
            else f"Insufficient data ({total} test cases, minimum 3 required for confidence)."
        )

        output[band_key.value] = BandMetrics(
            band=band_key,
            total_cases=total,
            passed_cases=passed,
            pass_rate=pass_rate,
            mean_latency_ms=mean_lat,
            has_sufficient_data=has_sufficient,
            insufficient_data_note=note,
        )

    return output
