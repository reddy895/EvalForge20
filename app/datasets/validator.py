"""Dataset schema, line-specific validation errors, and report generation."""

from pathlib import Path
from typing import Any
from pydantic import BaseModel, ConfigDict, Field

from app.datasets.parser import JSONLParseError, iter_jsonl_lines
from app.domain.dataset import DatasetStats
from app.domain.models import EvaluationCase


class DatasetValidationIssue(BaseModel):
    """Detailed error or warning found during dataset validation."""

    model_config = ConfigDict(frozen=True)

    line_number: int = Field(..., ge=1)
    case_id: str | None = Field(default=None)
    error_type: str = Field(..., description="e.g. MISSING_FIELD, INVALID_TYPE, MALFORMED_JSON, DUPLICATE_ID")
    message: str = Field(..., description="Human-readable explanation")


class DatasetValidationReport(BaseModel):
    """Complete validation report for a dataset file or stream."""

    model_config = ConfigDict(frozen=True)

    is_valid: bool
    total_lines_read: int = Field(default=0, ge=0)
    valid_cases_count: int = Field(default=0, ge=0)
    issues: list[DatasetValidationIssue] = Field(default_factory=list)
    cases: list[EvaluationCase] = Field(default_factory=list)
    stats: DatasetStats = Field(default_factory=DatasetStats)

    def format_errors(self) -> str:
        """Format line-specific validation errors into a human-readable list."""
        if not self.issues:
            return "Dataset is valid with 0 errors."
        lines: list[str] = [f"Found {len(self.issues)} issue(s) during dataset validation:"]
        for issue in self.issues:
            case_info = f" [id={issue.case_id}]" if issue.case_id else ""
            lines.append(f"  Line {issue.line_number}: [{issue.error_type}]{case_info} {issue.message}")
        return "\n".join(lines)


def validate_case_payload(
    line_number: int, payload: dict[str, Any]
) -> tuple[EvaluationCase | None, list[DatasetValidationIssue]]:
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


def parse_and_validate_lines(
    lines: list[str],
) -> tuple[list[EvaluationCase], list[DatasetValidationIssue], int]:
    """Parse raw lines and collect line-specific issues without stopping early."""
    import json

    all_issues: list[DatasetValidationIssue] = []
    valid_cases: list[EvaluationCase] = []
    total_non_empty = 0

    for line_number, line in enumerate(lines, start=1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        total_non_empty += 1
        try:
            payload = json.loads(stripped)
            if not isinstance(payload, dict):
                all_issues.append(
                    DatasetValidationIssue(
                        line_number=line_number,
                        case_id=None,
                        error_type="MALFORMED_JSON",
                        message=f"Expected JSON object, got {type(payload).__name__}",
                    )
                )
                continue
        except json.JSONDecodeError as exc:
            all_issues.append(
                DatasetValidationIssue(
                    line_number=line_number,
                    case_id=None,
                    error_type="MALFORMED_JSON",
                    message=f"JSON decoding error: {exc.msg} at col {exc.colno}",
                )
            )
            continue

        case, issues = validate_case_payload(line_number, payload)
        if issues:
            all_issues.extend(issues)
        elif case is not None:
            valid_cases.append(case)

    return valid_cases, all_issues, total_non_empty
