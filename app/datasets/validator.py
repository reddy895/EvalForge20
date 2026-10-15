"""Dataset schema, line-specific validation errors, duplicate-ID detection, and report generation."""

import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.domain.dataset import DatasetStats
from app.domain.models import EvaluationCase


class DatasetValidationIssue(BaseModel):
    """Detailed error or warning found during dataset validation."""

    model_config = ConfigDict(frozen=True)

    line_number: int = Field(..., ge=1)
    case_id: str | None = Field(default=None)
    error_type: str = Field(
        ..., description="e.g. MISSING_FIELD, INVALID_TYPE, MALFORMED_JSON, DUPLICATE_ID"
    )
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
            lines.append(
                f"  Line {issue.line_number}: [{issue.error_type}]{case_info} {issue.message}"
            )
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


def compute_dataset_stats(cases: list[EvaluationCase]) -> DatasetStats:
    """Compute aggregate categorical and feature distribution statistics."""
    categories: dict[str, int] = {}
    tags: dict[str, int] = {}
    with_expected = 0
    with_context = 0
    with_tools = 0

    for case in cases:
        if case.expected_output is not None:
            with_expected += 1
        if case.context:
            with_context += 1
        if case.tools:
            with_tools += 1

        if case.category:
            categories[case.category] = categories.get(case.category, 0) + 1

        for tag in case.tags:
            tags[tag] = tags.get(tag, 0) + 1

    return DatasetStats(
        total_cases=len(cases),
        cases_with_expected_output=with_expected,
        categories_distribution=categories,
        tags_distribution=tags,
        has_context_count=with_context,
        has_tools_count=with_tools,
    )


def validate_dataset(source: str | Path) -> DatasetValidationReport:
    """Parse a JSONL dataset file or content string, validating schema, types, and duplicate IDs."""
    if isinstance(source, Path):
        if not source.exists():
            return DatasetValidationReport(
                is_valid=False,
                issues=[
                    DatasetValidationIssue(
                        line_number=1,
                        case_id=None,
                        error_type="FILE_NOT_FOUND",
                        message=f"Dataset file not found: {source}",
                    )
                ],
            )
        lines = source.read_text(encoding="utf-8").splitlines()
    elif "\n" in source or "{" in source:
        lines = source.splitlines()
    else:
        path = Path(source)
        if not path.exists():
            return DatasetValidationReport(
                is_valid=False,
                issues=[
                    DatasetValidationIssue(
                        line_number=1,
                        case_id=None,
                        error_type="FILE_NOT_FOUND",
                        message=f"Dataset file not found: {path}",
                    )
                ],
            )
        lines = path.read_text(encoding="utf-8").splitlines()

    all_issues: list[DatasetValidationIssue] = []
    valid_cases: list[EvaluationCase] = []
    seen_ids: dict[str, int] = {}  # case_id -> line_number
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
            continue

        if case is not None:
            # Duplicate ID detection
            if case.id in seen_ids:
                first_line = seen_ids[case.id]
                all_issues.append(
                    DatasetValidationIssue(
                        line_number=line_number,
                        case_id=case.id,
                        error_type="DUPLICATE_ID",
                        message=f"Duplicate case identifier '{case.id}' (first declared on line {first_line})",
                    )
                )
            else:
                seen_ids[case.id] = line_number
                valid_cases.append(case)

    is_valid = len(all_issues) == 0 and total_non_empty > 0
    stats = (
        compute_dataset_stats(valid_cases)
        if is_valid
        else DatasetStats(total_cases=len(valid_cases))
    )

    if total_non_empty == 0 and not all_issues:
        all_issues.append(
            DatasetValidationIssue(
                line_number=1,
                case_id=None,
                error_type="EMPTY_DATASET",
                message="Dataset contains 0 valid test cases",
            )
        )
        is_valid = False

    return DatasetValidationReport(
        is_valid=is_valid,
        total_lines_read=total_non_empty,
        valid_cases_count=len(valid_cases),
        issues=all_issues,
        cases=valid_cases if is_valid else [],
        stats=stats,
    )
