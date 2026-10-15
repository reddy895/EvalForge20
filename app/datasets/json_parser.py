"""Standard JSON array dataset parser for EvalForge20."""

import json
from pathlib import Path
from typing import Any

from app.datasets.validator import DatasetValidationReport, ValidationErrorDetail
from app.domain.models import EvaluationCase


def parse_json_content(content: str, source_name: str = "<json_string>") -> DatasetValidationReport:
    """Parse JSON dataset text (array of cases or dict with 'cases' list)."""
    try:
        data = json.loads(content)
    except json.JSONDecodeError as exc:
        return DatasetValidationReport(
            is_valid=False,
            total_cases=0,
            valid_cases_count=0,
            invalid_cases_count=1,
            errors=[
                ValidationErrorDetail(
                    line_number=exc.lineno,
                    message=f"Invalid JSON syntax: {exc.msg}",
                    raw_line=content.splitlines()[exc.lineno - 1] if content.splitlines() else "",
                )
            ],
        )

    # Determine list of records
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
                total_cases=0,
                valid_cases_count=0,
                invalid_cases_count=1,
                errors=[
                    ValidationErrorDetail(
                        line_number=1,
                        message="Top-level JSON object must contain a 'cases' or 'data' array.",
                        raw_line=content[:100],
                    )
                ],
            )
    else:
        return DatasetValidationReport(
            is_valid=False,
            total_cases=0,
            valid_cases_count=0,
            invalid_cases_count=1,
            errors=[
                ValidationErrorDetail(
                    line_number=1,
                    message="JSON dataset must be a list of case objects or a dict with a 'cases' array.",
                    raw_line=content[:100],
                )
            ],
        )

    cases: list[EvaluationCase] = []
    errors: list[ValidationErrorDetail] = []
    seen_ids: dict[str, int] = {}

    for idx, item in enumerate(raw_records, start=1):
        if not isinstance(item, dict):
            errors.append(
                ValidationErrorDetail(
                    line_number=idx,
                    message=f"Item {idx} must be a JSON object, got {type(item).__name__}",
                    raw_line=str(item),
                )
            )
            continue

        raw_input = item.get("input") or item.get("prompt") or item.get("question")
        if raw_input is None or not str(raw_input).strip():
            errors.append(
                ValidationErrorDetail(
                    line_number=idx,
                    message="Missing required field 'input' (or 'prompt'/'question')",
                    raw_line=json.dumps(item),
                )
            )
            continue

        raw_id = item.get("id") or item.get("case_id")
        case_id = str(raw_id).strip() if raw_id else f"case_{idx}"

        if case_id in seen_ids:
            errors.append(
                ValidationErrorDetail(
                    line_number=idx,
                    message=f"Duplicate case id '{case_id}' (first seen at item {seen_ids[case_id]})",
                    raw_line=json.dumps(item),
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

        # Preserve context field in metadata if present at top-level
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

    return DatasetValidationReport(
        is_valid=len(errors) == 0,
        total_cases=len(raw_records),
        valid_cases_count=len(cases),
        invalid_cases_count=len(errors),
        cases=cases,
        errors=errors,
    )


def parse_json_file(path: Path | str) -> DatasetValidationReport:
    """Parse JSON dataset from a file path."""
    file_path = Path(path)
    if not file_path.exists():
        return DatasetValidationReport(
            is_valid=False,
            total_cases=0,
            valid_cases_count=0,
            invalid_cases_count=1,
            errors=[
                ValidationErrorDetail(
                    line_number=1, message=f"JSON file not found: {file_path}", raw_line=""
                )
            ],
        )

    content = file_path.read_text(encoding="utf-8")
    return parse_json_content(content, source_name=str(file_path))
