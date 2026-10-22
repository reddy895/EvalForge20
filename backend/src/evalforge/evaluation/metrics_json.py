"""JSON format and schema validity evaluator."""

import json
from typing import Any


def validate_json_validity(text: str) -> tuple[bool, Any | None, str | None]:
    """Check if model output contains syntactically valid JSON."""
    cleaned = text.strip()
    # Strip markdown codeblocks if present
    if cleaned.startswith("```json"):
        cleaned = cleaned[7:]
    if cleaned.startswith("```"):
        cleaned = cleaned[3:]
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]
    cleaned = cleaned.strip()

    try:
        parsed = json.loads(cleaned)
        return True, parsed, None
    except json.JSONDecodeError as err:
        return False, None, f"JSONDecodeError: {err.msg} at line {err.lineno}"
