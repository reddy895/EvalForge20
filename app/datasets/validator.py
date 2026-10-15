"""Dataset schema and required field validator."""

from typing import Any
from pydantic import BaseModel, ConfigDict, Field

from app.domain.models import EvaluationCase


class DatasetValidationIssue(BaseModel):
    """Detailed error or warning found during dataset validation."""

    model_config = ConfigDict(frozen=True)

    line_number: int = Field(..., ge=1)
    case_id: str | None = Field(default=None)
    error_type: str = Field(..., description="e.g. MISSING_FIELD, INVALID_TYPE, MALFORMED_JSON")
    message: str = Field(..., description="Human-readable explanation")


def validate_case_payload(line_number: int, payload: dict[str, Any]) -> tuple[EvaluationCase | None, list[DatasetValidationIssue]]:
    """Validate a single parsed JSON dictionary against the EvaluationCase contract."""
    issues: list[DatasetValidationIssue] = []

    # 1. Check ID
    raw_id = payload.get("id")
    if raw_id is None:
        issues.append(
            DatasetValidationIssue(
                line_number=line_number,
                case_id=None,
                error_type="MISSING_FIELD",
                message="Missing required field: 'id'",
            )
        )
    elif not isinstance(raw_id, str) or not raw_id.strip():
        issues.append(
            DatasetValidationIssue(
                line_number=line_number,
                case_id=str(raw_id) if raw_id is not None else None,
                error_type="INVALID_TYPE",
                message=f"Field 'id' must be a non-empty string, got {type(raw_id).__name__}",
            )
        )

    case_id_str = str(raw_id).strip() if isinstance(raw_id, str) and raw_id.strip() else None

    # 2. Check input
    raw_input = payload.get("input")
    if raw_input is None:
        issues.append(
            DatasetValidationIssue(
                line_number=line_number,
                case_id=case_id_str,
                error_type="MISSING_FIELD",
                message="Missing required field: 'input'",
            )
        )
    elif not isinstance(raw_input, str | dict):
        issues.append(
            DatasetValidationIssue(
                line_number=line_number,
                case_id=case_id_str,
                error_type="INVALID_TYPE",
                message=f"Field 'input' must be a string or object, got {type(raw_input).__name__}",
            )
        )

    # 3. Check expected_output (optional)
    raw_expected = payload.get("expected_output")
    if raw_expected is not None and not isinstance(raw_expected, str | dict | list):
        issues.append(
            DatasetValidationIssue(
                line_number=line_number,
                case_id=case_id_str,
                error_type="INVALID_TYPE",
                message=f"Field 'expected_output' must be string, object, or list, got {type(raw_expected).__name__}",
            )
        )

    # 4. Check tags
    raw_tags = payload.get("tags")
    tags_list: list[str] = []
    if raw_tags is not None:
        if not isinstance(raw_tags, list):
            issues.append(
                DatasetValidationIssue(
                    line_number=line_number,
                    case_id=case_id_str,
                    error_type="INVALID_TYPE",
                    message=f"Field 'tags' must be a list of strings, got {type(raw_tags).__name__}",
                )
            )
        else:
            tags_list = [str(t) for t in raw_tags]

    # 5. Check metadata
    raw_metadata = payload.get("metadata", {})
    if not isinstance(raw_metadata, dict):
        issues.append(
            DatasetValidationIssue(
                line_number=line_number,
                case_id=case_id_str,
                error_type="INVALID_TYPE",
                message=f"Field 'metadata' must be a dictionary, got {type(raw_metadata).__name__}",
            )
        )
        raw_metadata = {}

    if issues:
        return None, issues

    case = EvaluationCase(
        id=case_id_str,  # type: ignore[arg-type]
        input=raw_input,
        expected_output=raw_expected,
        metadata=raw_metadata,
        tags=tags_list,
        category=payload.get("category"),
        context=payload.get("context"),
        tools=payload.get("tools"),
        expected_tool_calls=payload.get("expected_tool_calls"),
    )
    return case, []
