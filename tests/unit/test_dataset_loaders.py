"""Unit tests for multi-format dataset loading (JSONL, JSON, CSV, In-Memory)."""

from pathlib import Path

import pytest
from app.datasets.loader import DatasetLoader
from app.domain.errors import DatasetValidationError


def test_load_sample_datasets():
    """Verify built-in sample datasets across all formats load successfully."""
    qa_cases = DatasetLoader.load_from_path("examples/datasets/qa_sample.json")
    assert len(qa_cases) == 3
    assert qa_cases[0].id == "qa-001"
    assert qa_cases[0].expected_output == "Tokyo"

    cls_cases = DatasetLoader.load_from_path("examples/datasets/classification_sample.csv")
    assert len(cls_cases) == 5
    assert cls_cases[0].category == "sentiment"
    assert cls_cases[0].expected_output == "positive"

    rag_cases = DatasetLoader.load_from_path("examples/datasets/rag_sample.jsonl")
    assert len(rag_cases) == 2
    assert "retrieved_chunks" in rag_cases[0].metadata

    agent_cases = DatasetLoader.load_from_path("examples/datasets/agent_sample.jsonl")
    assert len(agent_cases) == 2
    assert "expected_tools" in agent_cases[0].metadata


def test_csv_parser_custom_headers(tmp_path: Path):
    """Verify CSV loader adapts to various column headers."""
    csv_file = tmp_path / "custom.csv"
    csv_file.write_text(
        "Prompt,Target,Topic\nHello world,Greeting,Social\nWhat time is it?,Time inquiry,Utility\n"
    )

    report = DatasetLoader.validate_path(csv_file)
    assert report.is_valid is True
    assert len(report.cases) == 2
    assert report.cases[0].input == "Hello world"
    assert report.cases[0].expected_output == "Greeting"
    assert report.cases[0].category == "Social"
    # Auto-generated ID since 'id' was not in headers
    assert report.cases[0].id == "row_1"


def test_json_parser_dict_wrapper(tmp_path: Path):
    """Verify JSON loader handles dict wrapping a 'cases' array."""
    json_file = tmp_path / "wrapped.json"
    json_file.write_text(
        '{"cases": [{"id": "c1", "input": "test prompt", "output": "test answer"}]}'
    )

    cases = DatasetLoader.load_from_path(json_file)
    assert len(cases) == 1
    assert cases[0].id == "c1"
    assert cases[0].input == "test prompt"
    assert cases[0].expected_output == "test answer"


def test_in_memory_records_loader():
    """Verify loading from in-memory dictionary list."""
    records = [
        {"id": "m1", "input": "2 + 2", "expected_output": "4"},
        {"id": "m2", "input": "3 + 3", "expected_output": "6", "category": "math"},
    ]
    cases = DatasetLoader.load_from_records(records)
    assert len(cases) == 2
    assert cases[0].id == "m1"
    assert cases[1].category == "math"

    # In-memory validation error on duplicate ID
    dup_records = [
        {"id": "m1", "input": "one"},
        {"id": "m1", "input": "two"},
    ]
    with pytest.raises(DatasetValidationError, match="Duplicate case id"):
        DatasetLoader.load_from_records(dup_records)


def test_csv_missing_input_column(tmp_path: Path):
    """Verify CSV with no recognized input column fails validation gracefully."""
    invalid_csv = tmp_path / "bad.csv"
    invalid_csv.write_text("random_header,another_col\nval1,val2\n")

    report = DatasetLoader.validate_path(invalid_csv)
    assert report.is_valid is False
    assert any("Missing required input column" in str(iss.message) for iss in report.issues)
