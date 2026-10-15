"""Unit tests for the python -m evalforge module entry point."""

import subprocess
import sys


def test_python_m_evalforge_version():
    """Verify python -m evalforge version runs and outputs the version string."""
    result = subprocess.run(
        [sys.executable, "-m", "evalforge", "version"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    assert "EvalForge20 version:" in result.stdout


def test_python_m_evalforge_datasets_validate():
    """Verify python -m evalforge datasets validate works with sample JSON dataset."""
    result = subprocess.run(
        [sys.executable, "-m", "evalforge", "datasets", "validate", "examples/datasets/qa_sample.json"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    assert "Dataset is valid" in result.stdout
