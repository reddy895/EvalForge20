"""Deterministic dataset content fingerprinting using SHA-256."""

import hashlib
import json
from collections.abc import Sequence
from typing import Any


def compute_dataset_fingerprint(cases: Sequence[dict[str, Any]]) -> str:
    """Compute deterministic SHA-256 hash over canonical test case representation."""
    canonical_cases = []
    for c in cases:
        canonical_cases.append({
            "id": str(c.get("id", "")),
            "prompt": str(c.get("prompt", "")),
            "expected_output": str(c.get("expected_output", "")),
        })
    canonical_cases.sort(key=lambda x: x["id"])
    serialized = json.dumps(canonical_cases, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()
