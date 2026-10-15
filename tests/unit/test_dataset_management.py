"""Unit and integration tests for dataset management, hashing, and CLI validation."""

from pathlib import Path

from app.cli.main import cli_app
from app.datasets.hasher import compute_cases_hash
from app.datasets.validator import validate_dataset
from app.domain.models import EvaluationCase
from typer.testing import CliRunner

runner = CliRunner()


def test_validate_valid_dataset():
    """Verify validation of a compliant JSONL dataset."""
    path = Path("examples/datasets/basic.jsonl")
    report = validate_dataset(path)

    assert report.is_valid
    assert report.valid_cases_count == 4
    assert len(report.issues) == 0
    assert report.stats.total_cases == 4
    assert report.stats.cases_with_expected_output == 4
    assert "geography" in report.stats.categories_distribution
    assert "math" in report.stats.categories_distribution


def test_validate_invalid_dataset():
    """Verify line-specific error detection on malformed and schema-violating lines."""
    path = Path("examples/datasets/invalid_cases.jsonl")
    report = validate_dataset(path)

    assert not report.is_valid
    assert len(report.issues) >= 4

    error_lines = [issue.line_number for issue in report.issues]
    assert 2 in error_lines  # Malformed JSON
    assert 3 in error_lines  # Missing ID
    assert 4 in error_lines  # Empty string ID
    assert 5 in error_lines  # Invalid input type (integer instead of str/dict)


def test_duplicate_id_detection():
    """Verify duplicate case IDs are flagged with exact line numbers."""
    content = (
        '{"id":"dup-001","input":"First instance"}\n'
        '{"id":"unique-001","input":"Other case"}\n'
        '{"id":"dup-001","input":"Duplicate instance"}\n'
    )
    report = validate_dataset(content)

    assert not report.is_valid
    duplicate_issues = [i for i in report.issues if i.error_type == "DUPLICATE_ID"]
    assert len(duplicate_issues) == 1
    assert duplicate_issues[0].line_number == 3
    assert duplicate_issues[0].case_id == "dup-001"
    assert "first declared on line 1" in duplicate_issues[0].message


def test_stable_content_hash_invariance():
    """Verify SHA-256 content hash is invariant to case ordering."""
    case1 = EvaluationCase(id="a", input="Prompt A", expected_output="Out A")
    case2 = EvaluationCase(id="b", input="Prompt B", expected_output="Out B")

    hash_forward = compute_cases_hash([case1, case2])
    hash_reversed = compute_cases_hash([case2, case1])

    assert hash_forward == hash_reversed
    assert len(hash_forward) == 64


def test_cli_dataset_validate_valid():
    """Test CLI dataset validate on a valid file."""
    result = runner.invoke(cli_app, ["dataset", "validate", "examples/datasets/basic.jsonl"])
    assert result.exit_code == 0
    assert "Dataset is valid!" in result.stdout


def test_cli_dataset_validate_invalid():
    """Test CLI dataset validate on an invalid file."""
    result = runner.invoke(
        cli_app, ["dataset", "validate", "examples/datasets/invalid_cases.jsonl"]
    )
    assert result.exit_code == 1
    assert "Dataset validation failed" in result.stdout


def test_cli_dataset_inspect():
    """Test CLI dataset inspect command."""
    result = runner.invoke(cli_app, ["dataset", "inspect", "examples/datasets/basic.jsonl"])
    assert result.exit_code == 0
    assert "Dataset Inspection: basic.jsonl" in result.stdout
    assert "Total Test Cases" in result.stdout
