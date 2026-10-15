"""Unit tests for Markdown report generation and file export."""

from datetime import UTC, datetime
from pathlib import Path

from app.domain.models import TargetConfiguration, TargetType
from app.domain.results import AggregateMetrics, CaseResult, MetricResult
from app.domain.state import EvaluationRunStatus
from app.reporting.markdown_exporter import (
    export_markdown_report_to_file,
    generate_markdown_report,
)
from app.runner.config import EvaluationRunConfig, EvaluationRunRecord


def test_generate_markdown_report(tmp_path: Path):
    """Verify Markdown report content includes headers, metrics, local infrastructure note, and case samples."""
    record = EvaluationRunRecord(
        run_id="run_md_test_1",
        name="Markdown Test Benchmark",
        status=EvaluationRunStatus.COMPLETED,
        config=EvaluationRunConfig(
            run_id="run_md_test_1",
            dataset_version_hash="abcdef1234567890",
            target=TargetConfiguration(
                target_name="Ollama Qwen Target",
                target_type=TargetType.OLLAMA,
                provider_name="ollama",
                model_identifier="qwen2.5:3b",
            ),
        ),
        total_cases=2,
        completed_cases=2,
        failed_cases=0,
        started_at=datetime(2026, 10, 15, 12, 0, 0, tzinfo=UTC),
        completed_at=datetime(2026, 10, 15, 12, 0, 5, tzinfo=UTC),
    )

    aggregates = AggregateMetrics(
        total_cases=2,
        completed_cases=2,
        failed_cases=0,
        pass_rate=1.0,
        mean_latency_ms=145.2,
        p95_latency_ms=180.0,
        total_tokens=450,
        metric_averages={"exact_match": 1.0, "token_f1": 0.95},
        metric_pass_rates={"exact_match": 1.0, "token_f1": 1.0},
        category_performance={"general_qa": {"pass_rate": 1.0, "count": 2}},
    )

    case_results = [
        CaseResult(
            case_id="case_1",
            run_id="run_md_test_1",
            input="What is 2+2?",
            actual_output="4",
            expected_output="4",
            latency_ms=120.0,
            metrics=[
                MetricResult(
                    metric_id="exact_match",
                    metric_name="Exact Match",
                    score=1.0,
                    passed=True,
                )
            ],
        ),
        CaseResult(
            case_id="case_2",
            run_id="run_md_test_1",
            input="Name the capital of France.",
            actual_output="Paris",
            expected_output="Paris",
            latency_ms=170.4,
            metrics=[
                MetricResult(
                    metric_id="exact_match",
                    metric_name="Exact Match",
                    score=1.0,
                    passed=True,
                )
            ],
        ),
    ]

    md = generate_markdown_report(record, case_results, aggregates)

    # Assert critical sections
    assert "# Evaluation Report: Markdown Test Benchmark" in md
    assert "**Run ID:** `run_md_test_1`" in md
    assert "**Target Model:** `qwen2.5:3b`" in md
    assert "100.0%" in md
    assert "145.2 ms" in md
    assert "Exact Match" in md
    assert "Token F1" in md
    assert "Zero cloud API fees incurred" in md
    assert "case_1" in md
    assert "case_2" in md

    # Assert file export
    dest = tmp_path / "reports" / "report.md"
    written = export_markdown_report_to_file(dest, md)
    assert written.exists()
    assert written.read_text(encoding="utf-8") == md
