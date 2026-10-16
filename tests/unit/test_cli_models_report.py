"""Unit tests for models CLI command and multi-format report CLI commands."""

from pathlib import Path

from app.cli.main import cli_app
from app.domain.models import TargetConfiguration, TargetType
from app.domain.results import AggregateMetrics, CaseResult, MetricResult
from app.domain.state import EvaluationRunStatus
from app.providers.ollama_diagnostics import OllamaDiagnosticReport
from app.runner.config import EvaluationRunConfig, EvaluationRunRecord
from app.storage.database import get_db
from app.storage.repositories import EvaluationRepository
from typer.testing import CliRunner

runner = CliRunner()


def test_cli_models_offline(monkeypatch):
    """Test 'evalforge20 models' displays error and setup instructions when offline."""

    async def mock_diag(base_url: str):
        return OllamaDiagnosticReport(
            is_reachable=False,
            base_url=base_url,
            installed_models=[],
            setup_instructions=["Install Ollama: curl -fsSL https://ollama.com/install.sh | sh"],
        )

    monkeypatch.setattr("app.cli.models.diagnose_ollama", mock_diag)

    res = runner.invoke(cli_app, ["models", "list"])
    assert res.exit_code == 1
    assert "Ollama server is unreachable" in res.output
    assert "Install Ollama" in res.output


def test_cli_models_online(monkeypatch):
    """Test 'evalforge20 models' outputs table when models are present."""

    async def mock_diag(base_url: str):
        return OllamaDiagnosticReport(
            is_reachable=True,
            base_url=base_url,
            installed_models=["qwen2.5:3b"],
        )

    async def mock_detailed(self):
        return [
            {
                "name": "qwen2.5:3b",
                "parameter_size": "3B",
                "quantization_level": "Q4_K_M",
                "size_bytes": 1900000000,
                "modified_at": "2026-10-15T12:00:00Z",
            }
        ]

    monkeypatch.setattr("app.cli.models.diagnose_ollama", mock_diag)
    monkeypatch.setattr("app.cli.models.OllamaProvider.list_detailed_models", mock_detailed)

    res = runner.invoke(cli_app, ["models"])
    assert res.exit_code == 0
    assert "qwen2.5:3b" in res.output
    assert "3B" in res.output


def test_cli_models_check(monkeypatch):
    """Test 'evalforge20 models check' verifies presence or gives pull advice."""

    async def mock_diag(base_url: str):
        return OllamaDiagnosticReport(
            is_reachable=True,
            base_url=base_url,
            installed_models=["qwen2.5:3b"],
        )

    monkeypatch.setattr("app.cli.models.diagnose_ollama", mock_diag)

    # Success check
    res_ok = runner.invoke(cli_app, ["models", "check", "qwen2.5:3b"])
    assert res_ok.exit_code == 0
    assert "is locally installed and ready" in res_ok.output

    # Missing check
    res_missing = runner.invoke(cli_app, ["models", "check", "missing-model"])
    assert res_missing.exit_code == 1
    assert "ollama pull missing-model" in res_missing.output


def test_cli_report_markdown_and_csv_export(tmp_path: Path):
    """Test exporting Markdown and CSV reports via CLI."""
    db = next(get_db())
    repo = EvaluationRepository(db)

    run_id = "run_cli_export_1"
    record = EvaluationRunRecord(
        run_id=run_id,
        name="CLI Export Benchmark",
        status=EvaluationRunStatus.COMPLETED,
        config=EvaluationRunConfig(
            run_id=run_id,
            target=TargetConfiguration(
                target_name="Qwen Target",
                target_type=TargetType.OLLAMA,
                provider_name="ollama",
                model_identifier="qwen2.5:3b",
            ),
        ),
        total_cases=1,
        completed_cases=1,
        failed_cases=0,
    )
    repo.create_run(record)
    repo.update_run_completion(
        run_id=run_id,
        status=EvaluationRunStatus.COMPLETED,
        aggregates=AggregateMetrics(
            total_cases=1,
            completed_cases=1,
            failed_cases=0,
            pass_rate=1.0,
            mean_latency_ms=90.0,
        ),
        completed_at=record.started_at,
    )
    repo.save_case_result(
        CaseResult(
            case_id="c1",
            run_id=run_id,
            input="hi",
            actual_output="hello",
            metrics=[
                MetricResult(metric_id="exact_match", metric_name="EM", score=1.0, passed=True)
            ],
        )
    )

    # 1. Export markdown
    md_file = tmp_path / "report.md"
    res_md = runner.invoke(
        cli_app,
        ["report", "export", run_id, "--format", "markdown", "--output", str(md_file)],
    )
    assert res_md.exit_code == 0
    assert md_file.exists()
    assert "# Evaluation Report: CLI Export Benchmark" in md_file.read_text(encoding="utf-8")

    # 2. Export csv
    csv_file = tmp_path / "report.csv"
    res_csv = runner.invoke(
        cli_app,
        ["report", "export", run_id, "--format", "csv", "--output", str(csv_file)],
    )
    assert res_csv.exit_code == 0
    assert csv_file.exists()
    assert "case_id,run_id,model_identifier" in csv_file.read_text(encoding="utf-8")
