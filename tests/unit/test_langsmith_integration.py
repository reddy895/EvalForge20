"""Unit tests for LangSmith integration in disabled mode, missing credentials, and mocked scenarios."""

from unittest.mock import MagicMock

import pytest
from app.config import get_settings
from app.domain.models import EvaluationCase, TargetConfiguration
from app.domain.results import AggregateMetrics, CaseResult, MetricResult
from app.integrations.langsmith.client import get_langsmith_client
from app.integrations.langsmith.config import get_langsmith_status
from app.integrations.langsmith.dataset_sync import sync_dataset_to_langsmith
from app.integrations.langsmith.experiments import sync_run_to_langsmith
from app.integrations.langsmith.tracer import record_case_trace, trace_evaluation_run
from app.runner.config import EvaluationRunConfig, EvaluationRunRecord


def test_langsmith_disabled_by_default():
    """Verify that LangSmith integration is disabled by default without external requests."""
    settings = get_settings()
    assert not settings.is_langsmith_enabled
    assert get_langsmith_client() is None

    status = get_langsmith_status()
    assert not status.is_enabled
    assert status.connection_status == "disabled"


@pytest.mark.asyncio
async def test_trace_evaluation_run_noop_when_disabled():
    """Verify tracer executes cleanly as a no-op when LangSmith is disabled."""
    async with trace_evaluation_run("test_run", "run_123") as tr:
        assert tr["traced"] is False
        assert tr["run_id"] == "run_123"

    # Should not raise any error
    record_case_trace("run_123", "c1", inputs="hello", outputs="world")


def test_dataset_sync_raises_when_disabled():
    """Verify sync_dataset_to_langsmith raises clear exception when credentials not present."""
    cases = [EvaluationCase(id="c1", input="hello", expected_output="world")]
    with pytest.raises(ValueError) as exc_info:
        sync_dataset_to_langsmith(cases, dataset_name="test_dataset")
    assert "Cannot synchronize dataset: LangSmith is disabled" in str(exc_info.value)


def test_experiment_sync_skipped_when_disabled():
    """Verify sync_run_to_langsmith cleanly returns skipped status without error."""
    record = EvaluationRunRecord(
        run_id="run_1",
        name="test",
        config=EvaluationRunConfig(target=TargetConfiguration(target_name="m")),
    )
    res = sync_run_to_langsmith(record, [], AggregateMetrics())
    assert res["status"] == "skipped"


def test_mocked_successful_dataset_sync(monkeypatch: pytest.MonkeyPatch):
    """Verify successful dataset synchronization using a mocked LangSmith client."""
    mock_client = MagicMock()
    mock_ds = MagicMock()
    mock_ds.id = "ls_ds_12345"
    mock_client.create_dataset.return_value = mock_ds
    mock_client.read_dataset.side_effect = Exception("Not found")

    monkeypatch.setattr(
        "app.integrations.langsmith.dataset_sync.get_langsmith_client", lambda: mock_client
    )

    cases = [
        EvaluationCase(id="c1", input="France capital?", expected_output="Paris"),
        EvaluationCase(id="c2", input="Math 2+2?", expected_output="4"),
    ]
    result = sync_dataset_to_langsmith(cases, dataset_name="mocked_dataset")

    assert result["status"] == "success"
    assert result["dataset_id"] == "ls_ds_12345"
    assert result["synced_examples"] == 2
    mock_client.create_examples.assert_called_once()


def test_mocked_successful_experiment_sync(monkeypatch: pytest.MonkeyPatch):
    """Verify successful experiment publishing using a mocked LangSmith client."""
    mock_client = MagicMock()
    mock_parent = MagicMock()
    mock_parent.id = "ls_parent_999"
    mock_child = MagicMock()
    mock_child.id = "ls_child_111"
    mock_client.create_run.side_effect = [mock_parent, mock_child]

    monkeypatch.setattr(
        "app.integrations.langsmith.experiments.get_langsmith_client", lambda: mock_client
    )

    record = EvaluationRunRecord(
        run_id="run_100",
        name="Mocked Experiment",
        config=EvaluationRunConfig(target=TargetConfiguration(target_name="m")),
    )
    cases = [
        CaseResult(
            case_id="c1",
            run_id="run_100",
            input="hi",
            actual_output="hello",
            metrics=[
                MetricResult(
                    metric_id="exact_match", metric_name="Exact Match", score=1.0, passed=True
                )
            ],
        )
    ]
    aggs = AggregateMetrics(total_cases=1, completed_cases=1, pass_rate=1.0)

    res = sync_run_to_langsmith(record, cases, aggs)
    assert res["status"] == "success"
    assert res["langsmith_run_id"] == "ls_parent_999"
    assert res["logged_cases"] == 1
    mock_client.create_feedback.assert_called_once()
