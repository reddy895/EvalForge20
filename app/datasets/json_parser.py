"""Standard JSON array dataset parser for EvalForge20."""

import json
from pathlib import Path
from typing import Any

from app.datasets.validator import (
    DatasetValidationIssue,
    DatasetValidationReport,
    compute_dataset_stats,
)
from app.domain.dataset import DatasetStats
from app.domain.models import EvaluationCase


def parse_json_content(content: str, source_name: str = "<json_string>") -> DatasetValidationReport:
    """Parse JSON dataset text (array of cases or dict with 'cases' list)."""
    try:
        data = json.loads(content)
    except json.JSONDecodeError as exc:
        return DatasetValidationReport(
            is_valid=False,
            total_lines_read=0,
            valid_cases_count=0,
            issues=[
                DatasetValidationIssue(
                    line_number=exc.lineno,
                    error_type="MALFORMED_JSON",
                    message=f"Invalid JSON syntax: {exc.msg}",
                )
            ],
        )

    raw_records: list[Any] = []
    if isinstance(data, list):
        raw_records = data
    elif isinstance(data, dict):
        if "cases" in data and isinstance(data["cases"], list):
            raw_records = data["cases"]
        elif "data" in data and isinstance(data["data"], list):
            raw_records = data["data"]
        else:
            return DatasetValidationReport(
                is_valid=False,
                total_lines_read=0,
                valid_cases_count=0,
                issues=[
                    DatasetValidationIssue(
                        line_number=1,
                        error_type="INVALID_STRUCTURE",
                        message="Top-level JSON object must contain a 'cases' or 'data' array.",
                    )
                ],
            )
    else:
        return DatasetValidationReport(
            is_valid=False,
            total_lines_read=0,
            valid_cases_count=0,
            issues=[
                DatasetValidationIssue(
                    line_number=1,
                    error_type="INVALID_STRUCTURE",
                    message="JSON dataset must be a list of case objects or a dict with a 'cases' array.",
                )
            ],
        )

    cases: list[EvaluationCase] = []
    issues: list[DatasetValidationIssue] = []
    seen_ids: dict[str, int] = {}

    for idx, item in enumerate(raw_records, start=1):
        if not isinstance(item, dict):
            issues.append(
                DatasetValidationIssue(
                    line_number=idx,
                    error_type="INVALID_TYPE",
                    message=f"Item {idx} must be a JSON object, got {type(item).__name__}",
                )
            )
            continue

        raw_input = item.get("input") or item.get("prompt") or item.get("question")
        if raw_input is None or not str(raw_input).strip():
            issues.append(
                DatasetValidationIssue(
                    line_number=idx,
                    error_type="MISSING_FIELD",
                    message="Missing required field 'input' (or 'prompt'/'question')",
                )
            )
            continue

        raw_id = item.get("id") or item.get("case_id")
        case_id = str(raw_id).strip() if raw_id else f"case_{idx}"

        if case_id in seen_ids:
            issues.append(
                DatasetValidationIssue(
                    line_number=idx,
                    case_id=case_id,
                    error_type="DUPLICATE_ID",
                    message=f"Duplicate case id '{case_id}' (first seen at item {seen_ids[case_id]})",
                )
            )
            continue
        seen_ids[case_id] = idx

        exp_output = (
            item.get("expected_output")
            or item.get("output")
            or item.get("target")
            or item.get("answer")
        )
        category = item.get("category")
        tags = item.get("tags") if isinstance(item.get("tags"), list) else []
        metadata = item.get("metadata", {})
        if not isinstance(metadata, dict):
            metadata = {"raw_metadata": metadata}

        if "context" in item and "context" not in metadata:
            metadata["context"] = item["context"]

        case = EvaluationCase(
            id=case_id,
            input=str(raw_input).strip(),
            expected_output=str(exp_output).strip() if exp_output is not None else None,
            category=str(category).strip() if category else None,
            tags=[str(t) for t in tags],
            metadata=metadata,
        )
        cases.append(case)

    is_valid = len(issues) == 0 and len(raw_records) > 0
    stats = compute_dataset_stats(cases) if is_valid else DatasetStats(total_cases=len(cases))

    return DatasetValidationReport(
        is_valid=is_valid,
        total_lines_read=len(raw_records),
        valid_cases_count=len(cases),
        issues=issues,
        cases=cases if is_valid else [],
        stats=stats,
    )


def parse_json_file(path: Path | str) -> DatasetValidationReport:
    """Parse JSON dataset from a file path."""
    file_path = Path(path)
    if not file_path.exists():
        return DatasetValidationReport(
            is_valid=False,
            total_lines_read=0,
            valid_cases_count=0,
            issues=[
                DatasetValidationIssue(
                    line_number=1,
                    error_type="FILE_NOT_FOUND",
                    message=f"JSON file not found: {file_path}",
                )
            ],
        )

    content = file_path.read_text(encoding="utf-8")
    return parse_json_content(content, source_name=str(file_path))
