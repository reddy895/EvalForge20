"""Dataset management and serialization package."""

from src.evalforge.datasets.exporter import export_dataset_to_csv, export_dataset_to_jsonl
from src.evalforge.datasets.loader import DatasetLoader, ParsedDatasetRecord
from src.evalforge.datasets.registry import (
    BUILTIN_BENCHMARK_SUITES,
    BenchmarkRegistry,
    BenchmarkSuite,
    get_benchmark_registry,
)
from src.evalforge.datasets.validator import (
    ValidationReport,
    compute_dataset_fingerprint,
    validate_dataset_records,
)

__all__ = [
    "DatasetLoader",
    "ParsedDatasetRecord",
    "validate_dataset_records",
    "compute_dataset_fingerprint",
    "ValidationReport",
    "BenchmarkSuite",
    "BUILTIN_BENCHMARK_SUITES",
    "BenchmarkRegistry",
    "get_benchmark_registry",
    "export_dataset_to_csv",
    "export_dataset_to_jsonl",
]
