"""Dataset parsing, validation, and versioning for EvalForge20."""

from app.datasets.csv_parser import parse_csv_content, parse_csv_file
from app.datasets.hasher import compute_cases_hash
from app.datasets.json_parser import parse_json_content, parse_json_file
from app.datasets.loader import DatasetLoader
from app.datasets.parser import JSONLParseError, iter_jsonl_lines, write_jsonl
from app.datasets.validator import (
    DatasetValidationIssue,
    DatasetValidationReport,
    validate_dataset,
)
from app.domain.errors import DatasetValidationError

__all__ = [
    "DatasetLoader",
    "DatasetValidationError",
    "DatasetValidationIssue",
    "DatasetValidationReport",
    "JSONLParseError",
    "compute_cases_hash",
    "iter_jsonl_lines",
    "parse_csv_content",
    "parse_csv_file",
    "parse_json_content",
    "parse_json_file",
    "validate_dataset",
    "write_jsonl",
]
