"""Unit tests for dataset fingerprinting and integrity validation."""

from src.evalforge.datasets.fingerprint import compute_dataset_fingerprint
from src.evalforge.datasets.validator import validate_dataset_records


def test_fingerprint_deterministic() -> None:
    data_a = [{"id": "1", "prompt": "Hi", "expected_output": "Hello"}]
    data_b = [{"id": "1", "prompt": "Hi", "expected_output": "Hello"}]
    assert compute_dataset_fingerprint(data_a) == compute_dataset_fingerprint(data_b)

def test_dataset_validator() -> None:
    records = [
        {"id": "c1", "prompt": "Write a python function"},
        {"id": "c2", "prompt": ""},  # invalid
        {"id": "c1", "prompt": "Duplicate id"},  # duplicate
    ]
    report = validate_dataset_records(records)
    assert report.is_valid is False
    assert report.valid_records == 1
    assert len(report.errors) == 2
