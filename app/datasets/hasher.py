"""Stable content hashing and dataset version fingerprinting."""

import hashlib
import json
from pathlib import Path
from typing import Any

from app.domain.models import EvaluationCase


def canonical_json_dump(obj: Any) -> str:
    """Produce a deterministic, whitespace-normalized, key-sorted JSON string."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def compute_cases_hash(cases: list[EvaluationCase]) -> str:
    """Compute a reproducible SHA-256 hash of a list of evaluation cases.

    Cases are ordered deterministically by ID to ensure hash stability.
    """
    sorted_cases = sorted(cases, key=lambda c: c.id)
    hasher = hashlib.sha256()

    for case in sorted_cases:
        canonical_str = canonical_json_dump(case.model_dump())
        hasher.update(canonical_str.encode("utf-8"))

    return hasher.hexdigest()


def compute_dataset_hash(source: str | Path) -> str:
    """Compute SHA-256 hash directly from file or content string."""
    from app.datasets.validator import validate_dataset

    report = validate_dataset(source)
    if not report.is_valid:
        raise ValueError(f"Cannot compute hash for invalid dataset: {report.format_errors()}")

    return compute_cases_hash(report.cases)
