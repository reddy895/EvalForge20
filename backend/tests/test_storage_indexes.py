"""Unit tests verifying database column index declarations for high-throughput query performance."""

from src.evalforge.storage.base import TimestampMixin
from src.evalforge.storage.models.dataset import Dataset, TestCase
from src.evalforge.storage.models.evaluation import CaseResult, EvaluationRun


def test_evaluation_run_indexes():
    """Verify primary filter and foreign key columns have indexes on EvaluationRun."""
    table = EvaluationRun.__table__
    indexed_columns = {col.name for col in table.columns if col.index}
    assert "model_id" in indexed_columns
    assert "status" in indexed_columns
    assert "dataset_id" in indexed_columns
    assert "created_at" in indexed_columns


def test_case_result_indexes():
    """Verify evaluation_id and case_id have indexes on CaseResult."""
    table = CaseResult.__table__
    indexed_columns = {col.name for col in table.columns if col.index}
    assert "evaluation_id" in indexed_columns
    assert "case_id" in indexed_columns


def test_dataset_and_test_case_indexes():
    """Verify search and foreign key columns have indexes on Dataset and TestCase."""
    dataset_table = Dataset.__table__
    dataset_indexed = {col.name for col in dataset_table.columns if col.index}
    assert "name" in dataset_indexed
    assert "created_at" in dataset_indexed

    test_case_table = TestCase.__table__
    test_case_indexed = {col.name for col in test_case_table.columns if col.index}
    assert "dataset_id" in test_case_indexed
    assert "created_at" in test_case_indexed
