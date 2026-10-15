"""Unit tests for security controls, secret redaction, and data retention boundaries."""

from datetime import UTC, datetime

from app.domain.models import TargetConfiguration
from app.domain.results import AggregateMetrics, CaseResult, MetricResult
from app.domain.state import EvaluationRunStatus
from app.logging import SecretRedactionFilter
from app.reporting.json_exporter import generate_json_report
from app.runner.config import EvaluationRunConfig, EvaluationRunRecord


def test_secret_redaction_filter():
    """Verify regex pattern redaction for API keys, bearer tokens, and secrets."""
    filter_ = SecretRedactionFilter()

    # Bearer tokens & explicit keys
    sample_log = "Error connecting to provider with api_key='sk-1234567890abcdef' and Authorization: Bearer secrettoken123"
    redacted = filter_.redact_text(sample_log)
    assert "sk-1234567890abcdef" not in redacted
    assert "secrettoken123" not in redacted
    assert "[REDACTED]" in redacted

    # LangSmith keys
    ls_log = "LangSmith client initialized with api_key: ls__9876543210abcdef"
    redacted_ls = filter_.redact_text(ls_log)
    assert "ls__9876543210abcdef" not in redacted_ls
    assert "[REDACTED]" in redacted_ls


def test_report_data_redaction():
    """Verify that sensitive user prompts and raw model outputs can be redacted in reports."""
    record = EvaluationRunRecord(
        run_id="run_sec_test",
        name="Security Test Run",
        status=EvaluationRunStatus.COMPLETED,
        config=EvaluationRunConfig(
            run_id="run_sec_test",
            name="Security Test",
            target=TargetConfiguration(target_name="mock_target", provider="mock", model="echo"),
            dataset_path="examples/datasets/basic.jsonl",
            dataset_version_hash="hash123",
        ),
        total_cases=1,
        completed_cases=1,
        started_at=datetime.now(UTC),
        completed_at=datetime.now(UTC),
    )

    case = CaseResult(
        case_id="case_1",
        run_id="run_sec_test",
        input="Confidential financial prompt for patient John Doe",
        actual_output="Private internal health diagnosis report",
        latency_ms=45.0,
        metrics=[
            MetricResult(metric_id="exact_match", metric_name="Exact Match", score=1.0, passed=True)
        ],
    )

    aggregates = AggregateMetrics(
        run_id="run_sec_test",
        total_cases=1,
        completed_cases=1,
        pass_rate=1.0,
    )

    # 1. Unredacted report
    plain_report = generate_json_report(
        record, [case], aggregates, redact_inputs=False, redact_outputs=False
    )
    assert (
        plain_report["per_case_results"][0]["input"]
        == "Confidential financial prompt for patient John Doe"
    )
    assert (
        plain_report["per_case_results"][0]["actual_output"]
        == "Private internal health diagnosis report"
    )

    # 2. Redacted report
    redacted_report = generate_json_report(
        record, [case], aggregates, redact_inputs=True, redact_outputs=True
    )
    assert redacted_report["per_case_results"][0]["input"] == "[REDACTED_PROMPT]"
    assert redacted_report["per_case_results"][0]["actual_output"] == "[REDACTED_OUTPUT]"
    assert "John Doe" not in str(redacted_report["per_case_results"])
