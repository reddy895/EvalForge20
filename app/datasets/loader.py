"""Unified dataset loader supporting JSONL, JSON, CSV, and in-memory evaluation cases."""

from pathlib import Path
from typing import Any

from app.datasets.csv_parser import parse_csv_content, parse_csv_file
from app.datasets.json_parser import parse_json_content, parse_json_file
from app.datasets.validator import (
    DatasetValidationReport,
    validate_dataset,
)
from app.domain.errors import DatasetValidationError
from app.domain.models import EvaluationCase
from app.security import validate_safe_path


class DatasetLoader:
    """Unified loader for local evaluation datasets across all supported formats."""

    @classmethod
    def detect_format(cls, path: Path | str) -> str:
        """Infer dataset format from file extension."""
        suffix = Path(path).suffix.lower()
        if suffix in (".jsonl", ".ndjson"):
            return "jsonl"
        elif suffix == ".csv":
            return "csv"
        elif suffix == ".json":
            return "json"
        raise ValueError(
            f"Unsupported dataset format '{suffix}'. Supported formats are: .jsonl, .json, .csv"
        )

    @classmethod
    def load(cls, path: Path | str, format: str | None = None) -> DatasetValidationReport:
        """Load and validate dataset from file path, returning DatasetValidationReport."""
        return cls.validate_path(path, format=format)

    @classmethod
    def validate_path(cls, path: Path | str, format: str | None = None) -> DatasetValidationReport:
        """Validate dataset file and return validation report."""
        target_path = validate_safe_path(path)
        fmt = (format or cls.detect_format(target_path)).lower()

        if fmt == "jsonl":
            return validate_dataset(target_path)
        elif fmt == "csv":
            return parse_csv_file(target_path)
        elif fmt == "json":
            return parse_json_file(target_path)
        else:
            raise ValueError(f"Unknown format '{fmt}'. Must be 'jsonl', 'csv', or 'json'.")

    @classmethod
    def validate_content(cls, content: str, format: str = "jsonl") -> DatasetValidationReport:
        """Validate raw dataset text content for a given format."""
        fmt = format.lower()
        if fmt == "jsonl":
            return validate_dataset(content)

        elif fmt == "csv":
            return parse_csv_content(content)
        elif fmt == "json":
            return parse_json_content(content)
        else:
            raise ValueError(f"Unknown format '{fmt}'. Must be 'jsonl', 'csv', or 'json'.")

    @classmethod
    def load_from_path(cls, path: Path | str, format: str | None = None) -> list[EvaluationCase]:
        """Load and validate dataset from file path, raising DatasetValidationError if invalid."""
        report = cls.validate_path(path, format=format)
        if not report.is_valid:
            raise DatasetValidationError(report.format_errors())
        return report.cases

    @classmethod
    def load_from_records(cls, records: list[dict[str, Any]]) -> list[EvaluationCase]:
        """Convert a list of in-memory dictionaries into validated EvaluationCase objects."""
        cases: list[EvaluationCase] = []
        errors: list[str] = []
        seen_ids: dict[str, int] = {}

        for idx, rec in enumerate(records, start=1):
            raw_input = rec.get("input") or rec.get("prompt") or rec.get("question")
            if not raw_input or not str(raw_input).strip():
                errors.append(f"Record {idx}: Missing required 'input' field")
                continue

            case_id = str(rec.get("id") or rec.get("case_id") or f"case_{idx}").strip()
            if case_id in seen_ids:
                errors.append(
                    f"Record {idx}: Duplicate case id '{case_id}' (first seen at record {seen_ids[case_id]})"
                )
                continue
            seen_ids[case_id] = idx

            exp_out = (
                rec.get("expected_output")
                or rec.get("output")
                or rec.get("target")
                or rec.get("answer")
            )
            category = rec.get("category")
            tags = (
                [str(t) for t in rec.get("tags", [])] if isinstance(rec.get("tags"), list) else []
            )
            metadata = rec.get("metadata", {})
            if not isinstance(metadata, dict):
                metadata = {"raw": metadata}
            if "context" in rec and "context" not in metadata:
                metadata["context"] = rec["context"]

            cases.append(
                EvaluationCase(
                    id=case_id,
                    input=str(raw_input).strip(),
                    expected_output=str(exp_out).strip() if exp_out is not None else None,
                    category=str(category).strip() if category else None,
                    tags=tags,
                    metadata=metadata,
                )
            )

        if errors:
            raise DatasetValidationError(
                "In-memory dataset validation failed:\n" + "\n".join(errors)
            )

        return cases
