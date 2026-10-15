"""CSV dataset parser with flexible column header mapping and line error tracking."""

import csv
import io
from pathlib import Path
from typing import Any

from app.datasets.validator import (
    DatasetValidationIssue,
    DatasetValidationReport,
    compute_dataset_stats,
)
from app.domain.dataset import DatasetStats
from app.domain.models import EvaluationCase

# Candidate column names in order of preference
INPUT_CANDIDATES = ("input", "prompt", "question", "query", "text", "instruction")
OUTPUT_CANDIDATES = (
    "expected_output",
    "output",
    "target",
    "ground_truth",
    "label",
    "answer",
    "reference",
)
ID_CANDIDATES = ("id", "case_id", "example_id", "row_id", "index")
CATEGORY_CANDIDATES = ("category", "topic", "domain", "slice")
CONTEXT_CANDIDATES = ("context", "retrieved_context", "passages")


def _find_matching_header(headers: list[str], candidates: tuple[str, ...]) -> str | None:
    """Find the first column header matching any candidate name case-insensitively."""
    lookup = {h.strip().lower(): h for h in headers if h}
    for cand in candidates:
        if cand.lower() in lookup:
            return lookup[cand.lower()]
    return None


def parse_csv_content(content: str, source_name: str = "<csv_string>") -> DatasetValidationReport:
    """Parse CSV text content into validated EvaluationCase list with line-level error reporting."""
    reader = csv.reader(io.StringIO(content))
    cases: list[EvaluationCase] = []
    issues: list[DatasetValidationIssue] = []
    seen_ids: dict[str, int] = {}
    total_lines = 0

    try:
        raw_headers = next(reader, None)
    except Exception as exc:
        return DatasetValidationReport(
            is_valid=False,
            total_lines_read=0,
            valid_cases_count=0,
            issues=[
                DatasetValidationIssue(
                    line_number=1, error_type="MALFORMED_CSV", message=f"CSV read error: {exc}"
                )
            ],
        )

    if raw_headers is None:
        return DatasetValidationReport(
            is_valid=False,
            total_lines_read=0,
            valid_cases_count=0,
            issues=[
                DatasetValidationIssue(
                    line_number=1, error_type="EMPTY_DATASET", message="Empty CSV dataset file"
                )
            ],
        )

    headers = [h.strip() for h in raw_headers]
    input_col = _find_matching_header(headers, INPUT_CANDIDATES)
    output_col = _find_matching_header(headers, OUTPUT_CANDIDATES)
    id_col = _find_matching_header(headers, ID_CANDIDATES)
    category_col = _find_matching_header(headers, CATEGORY_CANDIDATES)
    context_col = _find_matching_header(headers, CONTEXT_CANDIDATES)

    if not input_col:
        return DatasetValidationReport(
            is_valid=False,
            total_lines_read=0,
            valid_cases_count=0,
            issues=[
                DatasetValidationIssue(
                    line_number=1,
                    error_type="MISSING_FIELD",
                    message=f"Missing required input column in CSV headers {headers}. Expected one of {INPUT_CANDIDATES}",
                )
            ],
        )

    for line_num, row in enumerate(reader, start=2):
        if not row or all(not cell.strip() for cell in row):
            continue

        total_lines += 1

        if len(row) != len(headers):
            issues.append(
                DatasetValidationIssue(
                    line_number=line_num,
                    error_type="INVALID_ROW",
                    message=f"Row has {len(row)} values, but header specifies {len(headers)} columns",
                )
            )
            continue

        row_dict = dict(zip(headers, row, strict=False))
        inp = row_dict.get(input_col, "").strip()
        if not inp:
            issues.append(
                DatasetValidationIssue(
                    line_number=line_num,
                    error_type="MISSING_FIELD",
                    message=f"Input column '{input_col}' cannot be empty",
                )
            )
            continue

        case_id = row_dict.get(id_col, "").strip() if id_col else ""
        if not case_id:
            case_id = f"row_{line_num - 1}"

        if case_id in seen_ids:
            issues.append(
                DatasetValidationIssue(
                    line_number=line_num,
                    case_id=case_id,
                    error_type="DUPLICATE_ID",
                    message=f"Duplicate case id '{case_id}' (first seen at line {seen_ids[case_id]})",
                )
            )
            continue
        seen_ids[case_id] = line_num

        exp_out = row_dict.get(output_col, "").strip() if output_col else None
        cat = row_dict.get(category_col, "").strip() if category_col else None
        ctx = row_dict.get(context_col, "").strip() if context_col else None

        meta: dict[str, Any] = {}
        if ctx:
            meta["context"] = ctx

        standard_cols = {input_col, output_col, id_col, category_col, context_col}
        for k, v in row_dict.items():
            if k not in standard_cols and v.strip():
                meta[k] = v.strip()

        case = EvaluationCase(
            id=case_id,
            input=inp,
            expected_output=exp_out if exp_out else None,
            category=cat if cat else None,
            metadata=meta,
        )
        cases.append(case)

    is_valid = len(issues) == 0 and total_lines > 0
    stats = compute_dataset_stats(cases) if is_valid else DatasetStats(total_cases=len(cases))
    return DatasetValidationReport(
        is_valid=is_valid,
        total_lines_read=total_lines,
        valid_cases_count=len(cases),
        issues=issues,
        cases=cases if is_valid else [],
        stats=stats,
    )


def parse_csv_file(path: Path | str) -> DatasetValidationReport:
    """Parse CSV dataset from a file path."""
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
                    message=f"CSV file not found: {file_path}",
                )
            ],
        )

    content = file_path.read_text(encoding="utf-8")
    return parse_csv_content(content, source_name=str(file_path))
