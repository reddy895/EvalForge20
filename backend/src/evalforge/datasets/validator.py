"""Dataset schema and integrity validator with line-level error reporting and fingerprinting."""

import hashlib
import json
from dataclasses import dataclass
from typing import Any


@dataclass
class ValidationReport:
    is_valid: bool
    total_records: int
    valid_records: int
    records_with_reference: int
    fingerprint: str
    preview_samples: list[dict[str, Any]]
    errors: list[str]
    warnings: list[str]


def compute_dataset_fingerprint(records: list[dict[str, Any]]) -> str:
    """Compute deterministic SHA-256 hash of dataset items."""
    hasher = hashlib.sha256()
    for r in sorted(records, key=lambda x: str(x.get("id", x.get("input", x.get("prompt", ""))))):
        serialized = json.dumps(r, sort_keys=True, default=str)
        hasher.update(serialized.encode("utf-8"))
    return hasher.hexdigest()[:16]


def validate_dataset_records(records: list[dict[str, Any]]) -> ValidationReport:
    """Ensure records have non-empty input/prompt, unique identifier, and check reference answers."""
    seen_ids = set()
    errors = []
    warnings = []
    valid_count = 0
    with_ref_count = 0

    for idx, r in enumerate(records, start=1):
        case_id = str(r.get("id", f"case_{idx}"))
        if case_id in seen_ids:
            errors.append(f"Line {idx}: Duplicate case identifier '{case_id}'")
            continue
        seen_ids.add(case_id)

        prompt = str(r.get("input", r.get("prompt", ""))).strip()
        if not prompt:
            errors.append(f"Line {idx}: Missing or empty 'input' or 'prompt' field")
            continue

        ref = r.get("expected_output", r.get("expected_answer", r.get("reference")))
        if ref not in (None, ""):
            with_ref_count += 1
        else:
            warnings.append(f"Line {idx}: No expected answer provided (subjective/open-ended only)")

        valid_count += 1

    fingerprint = compute_dataset_fingerprint(records) if records else "empty"
    previews = [dict(r) for r in records[:3]]

    return ValidationReport(
        is_valid=len(errors) == 0 and valid_count > 0,
        total_records=len(records),
        valid_records=valid_count,
        records_with_reference=with_ref_count,
        fingerprint=fingerprint,
        preview_samples=previews,
        errors=errors,
        warnings=warnings[:10],
    )
