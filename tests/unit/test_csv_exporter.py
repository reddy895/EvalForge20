"""Unit tests for CSV per-case evaluation results exporter."""

import csv
import io
from pathlib import Path

from app.domain.models import TargetConfiguration, TargetType
from app.domain.results import CaseResult, MetricResult
from app.domain.state import EvaluationRunStatus
from app.reporting.csv_exporter import export_csv_report_to_file, generate_csv_report
from app.runner.config import EvaluationRunConfig, EvaluationRunRecord


def test_generate_csv_report(tmp_path: Path):
    """Verify CSV export produces correct header structure and row values with dynamic metrics."""
    record = EvaluationRunRecord(
        run_id="run_csv_test_1",
        name="CSV Test Run",
        status=EvaluationRunStatus.COMPLETED,
        config=EvaluationRunConfig(
            run_id="run_csv_test_1",
            target=TargetConfiguration(
                target_name="Qwen Target",
                target_type=TargetType.OLLAMA,
                provider_name="ollama",
                model_identifier="qwen2.5:3b",
            ),
        ),
    )

    case_results = [
        CaseResult(
            case_id="case_101",
            run_id="run_csv_test_1",
            input="What is the capital of Japan?",
            expected_output="Tokyo",
            actual_output="Tokyo",
            latency_ms=95.5,
            token_usage={"total_tokens": 12},
            metrics=[
                MetricResult(
                    metric_id="exact_match",
                    metric_name="Exact Match",
                    score=1.0,
                    passed=True,
                ),
                MetricResult(
                    metric_id="token_f1",
                    metric_name="Token F1",
                    score=1.0,
                    passed=True,
                ),
            ],
        ),
        CaseResult(
            case_id="case_102",
            run_id="run_csv_test_1",
            input="What is 10 * 10?",
            expected_output="100",
            actual_output="1000",
            latency_ms=110.0,
            token_usage={"total_tokens": 15},
            metrics=[
                MetricResult(
                    metric_id="exact_match",
                    metric_name="Exact Match",
                    score=0.0,
                    passed=False,
                ),
                MetricResult(
                    metric_id="token_f1",
                    metric_name="Token F1",
                    score=0.0,
                    passed=False,
                ),
            ],
        ),
    ]

    csv_text = generate_csv_report(record, case_results)

    reader = csv.reader(io.StringIO(csv_text))
    rows = list(reader)

    # 1 header row + 2 data rows
    assert len(rows) == 3

    headers = rows[0]
    assert headers[:4] == ["case_id", "run_id", "model_identifier", "input"]
    assert "exact_match_score" in headers
    assert "exact_match_passed" in headers
    assert "token_f1_score" in headers
    assert "token_f1_passed" in headers

    row1 = rows[1]
    assert row1[0] == "case_101"
    assert row1[1] == "run_csv_test_1"
    assert row1[2] == "qwen2.5:3b"
    assert row1[6] == "True"  # passed
    assert row1[7] == "95.5"  # latency

    row2 = rows[2]
    assert row2[0] == "case_102"
    assert row2[6] == "False"  # passed

    # File export test
    dest = tmp_path / "exports" / "cases.csv"
    saved = export_csv_report_to_file(dest, csv_text)
    assert saved.exists()
    assert saved.read_text(encoding="utf-8") == csv_text
