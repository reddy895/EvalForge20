"""Dataset schema and integrity validator with line-level error reporting."""

from dataclasses import dataclass
from typing import Any


@dataclass
class ValidationReport:
    is_valid: bool
    total_records: int
    valid_records: int
    errors: list[str]

def validate_dataset_records(records: list[dict[str, Any]]) -> ValidationReport:
    """Ensure records have non-empty prompt and unique identifier."""
    seen_ids = set()
    errors = []
    valid_count = 0

    for idx, r in enumerate(records, start=1):
        case_id = str(r.get("id", f"case_{idx}"))
        if case_id in seen_ids:
            errors.append(f"Line {idx}: Duplicate case identifier '{case_id}'")
            continue
        seen_ids.add(case_id)

        prompt = str(r.get("prompt", "")).strip()
        if not prompt:
            errors.append(f"Line {idx}: Missing or empty 'prompt' field")
            continue

        valid_count += 1

    return ValidationReport(
        is_valid=len(errors) == 0,
        total_records=len(records),
        valid_records=valid_count,
        errors=errors,
    )
