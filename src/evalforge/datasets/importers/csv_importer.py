"""CSV and TSV dataset importer with automatic delimiter sniffing and column mapping."""

import csv
import io

from src.evalforge.schemas.dataset import RowImportError, TestCaseCreate


def parse_csv_content(content: str) -> tuple[list[TestCaseCreate], list[RowImportError]]:
    """Parse CSV or TSV content into validated TestCaseCreate models."""
    valid_cases: list[TestCaseCreate] = []
    errors: list[RowImportError] = []

    if not content.strip():
        return valid_cases, errors

    # Auto-detect delimiter
    sample = content[:2048]
    delimiter = ","
    try:
        sniffer = csv.Sniffer()
        dialect = sniffer.sniff(sample, delimiters=",\t;|")
        delimiter = dialect.delimiter
    except Exception:
        delimiter = "\t" if "\t" in sample and "," not in sample else ","

    reader = csv.DictReader(io.StringIO(content), delimiter=delimiter)
    if not reader.fieldnames:
        errors.append(
            RowImportError(
                line=1,
                raw_data=content[:100],
                error="CSV has no header row or columns defined",
            )
        )
        return valid_cases, errors

    # Normalize header mapping
    header_map = {fn.strip().lower(): fn for fn in reader.fieldnames if fn}

    prompt_col = None
    for candidate in ("prompt", "input", "question", "instruction", "query"):
        if candidate in header_map:
            prompt_col = header_map[candidate]
            break

    if not prompt_col:
        errors.append(
            RowImportError(
                line=1,
                raw_data=str(reader.fieldnames),
                error="CSV must contain a 'prompt' (or 'input'/'question'/'instruction') column",
            )
        )
        return valid_cases, errors

    expected_col = None
    for candidate in ("expected_output", "target", "answer", "ground_truth", "expected"):
        if candidate in header_map:
            expected_col = header_map[candidate]
            break

    context_col = None
    for candidate in ("context", "document", "reference"):
        if candidate in header_map:
            context_col = header_map[candidate]
            break

    tags_col = header_map.get("tags")

    # Read rows
    for row_idx, row in enumerate(reader, start=2):
        try:
            raw_prompt = (row.get(prompt_col) or "").strip()
            if not raw_prompt:
                errors.append(
                    RowImportError(
                        line=row_idx,
                        raw_data=str(row)[:100],
                        error=f"Row has empty '{prompt_col}'",
                    )
                )
                continue

            expected = (
                row.get(expected_col).strip() if expected_col and row.get(expected_col) else None
            )
            context = row.get(context_col).strip() if context_col and row.get(context_col) else None

            tags: list[str] = []
            if tags_col and row.get(tags_col):
                tags = [t.strip() for t in row[tags_col].split(",") if t.strip()]

            # Collect any leftover columns into metadata
            metadata = {}
            for col, val in row.items():
                if col not in (prompt_col, expected_col, context_col, tags_col) and val:
                    metadata[col] = val

            test_case = TestCaseCreate(
                prompt=raw_prompt,
                expected_output=expected,
                context=context,
                tags=tags,
                metadata=metadata,
            )
            valid_cases.append(test_case)

        except Exception as exc:
            errors.append(
                RowImportError(
                    line=row_idx,
                    raw_data=str(row)[:100],
                    error=f"Row parsing failed: {exc}",
                )
            )

    return valid_cases, errors
