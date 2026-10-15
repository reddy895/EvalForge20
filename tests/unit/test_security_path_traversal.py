"""Unit tests for path traversal validation and system directory protection."""

from pathlib import Path

import pytest
from app.datasets.loader import DatasetLoader
from app.reporting.csv_exporter import export_csv_report_to_file
from app.reporting.json_exporter import export_report_to_file
from app.reporting.markdown_exporter import export_markdown_report_to_file
from app.security import validate_safe_path


def test_validate_safe_path_valid(tmp_path: Path):
    """Test valid paths resolve correctly within allowed directories."""
    valid_file = tmp_path / "dataset.jsonl"
    valid_file.write_text('{"input": "hi"}')

    resolved = validate_safe_path(valid_file, base_dir=tmp_path)
    assert resolved == valid_file.resolve()


def test_validate_safe_path_blocks_system_dirs():
    """Test accessing restricted system directories raises ValueError."""
    with pytest.raises(ValueError, match="Access to system directory '/etc' is restricted"):
        validate_safe_path("/etc/passwd")

    with pytest.raises(ValueError, match="Access to system directory '/etc' is restricted"):
        validate_safe_path("/etc/shadow")

    with pytest.raises(ValueError, match="Access to system directory '/root' is restricted"):
        validate_safe_path("/root/.ssh/id_rsa")


def test_validate_safe_path_blocks_directory_escape(tmp_path: Path):
    """Test path traversal escaping base directory raises ValueError."""
    sandbox = tmp_path / "sandbox"
    sandbox.mkdir()

    traversal_path = sandbox / ".." / "escaped.txt"

    with pytest.raises(ValueError, match="Path traversal detected"):
        validate_safe_path(traversal_path, base_dir=sandbox)


def test_dataset_loader_blocks_system_directory_traversal():
    """Verify DatasetLoader blocks loading from system paths."""
    with pytest.raises(ValueError, match="Access to system directory '/etc' is restricted"):
        DatasetLoader.validate_path("/etc/passwd")


def test_exporters_block_system_directory_traversal():
    """Verify JSON, Markdown, and CSV exporters block writing to system directories."""
    with pytest.raises(ValueError, match="Access to system directory '/etc' is restricted"):
        export_report_to_file("/etc/evalforge_report.json", {})

    with pytest.raises(ValueError, match="Access to system directory '/etc' is restricted"):
        export_markdown_report_to_file("/etc/evalforge_report.md", "# Report")

    with pytest.raises(ValueError, match="Access to system directory '/etc' is restricted"):
        export_csv_report_to_file("/etc/evalforge_report.csv", "a,b,c")
