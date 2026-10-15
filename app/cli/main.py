"""Main entrypoint for the EvalForge20 command line interface."""

from pathlib import Path

import typer

from app import __version__
from app.cli.datasets import dataset_cli
from app.cli.langsmith import langsmith_cli
from app.cli.providers import provider_cli
from app.cli.report import report_cli
from app.cli.runs import run_evaluation_cli, runs_cli

cli_app = typer.Typer(
    name="evalforge20",
    help="EvalForge20: Production-minded, local-first LLM & AI agent evaluation platform.",
    add_completion=False,
)

# Register sub-commands
cli_app.add_typer(dataset_cli, name="dataset")
cli_app.add_typer(provider_cli, name="provider")
cli_app.add_typer(runs_cli, name="runs")
cli_app.add_typer(report_cli, name="report")
cli_app.add_typer(langsmith_cli, name="langsmith")


@cli_app.command(name="evaluate")
def evaluate_command(
    dataset: Path = typer.Option(..., "--dataset", "-d", help="Path to JSONL dataset", exists=True),
    provider: str = typer.Option(
        "mock", "--provider", "-p", help="Provider name (e.g. ollama, mock)"
    ),
    model: str = typer.Option("mock-model-v1", "--model", "-m", help="Model identifier"),
    metrics: str = typer.Option(
        "exact_match,normalized_match", "--metrics", help="Comma-separated metric IDs"
    ),
    concurrency: int = typer.Option(5, "--concurrency", "-c", help="Max concurrent cases"),
    retries: int = typer.Option(2, "--retries", "-r", help="Max retries for transient errors"),
    timeout: float = typer.Option(60.0, "--timeout", "-t", help="Timeout per request in seconds"),
    name: str = typer.Option("CLI Evaluation Run", "--name", "-n", help="Human-readable run name"),
) -> None:
    """Execute an evaluation run from terminal."""
    run_evaluation_cli(
        dataset=dataset,
        provider=provider,
        model=model,
        metrics=metrics,
        concurrency=concurrency,
        retries=retries,
        timeout=timeout,
        name=name,
    )


@cli_app.command(name="compare")
def compare_command(
    baseline_run_id: str = typer.Argument(..., help="Baseline run ID"),
    candidate_run_id: str = typer.Argument(..., help="Candidate run ID to compare against baseline"),
    max_drop: float = typer.Option(0.05, "--max-drop", help="Max allowed drop in pass rate (e.g. 0.05)"),
    max_latency_increase: float = typer.Option(250.0, "--max-latency-increase", help="Max latency increase in ms"),
    allow_different_datasets: bool = typer.Option(False, "--allow-different-datasets", help="Allow comparison across different datasets"),
) -> None:
    """Compare candidate evaluation run against baseline benchmark and check regressions."""
    from rich.console import Console
    from rich.table import Table

    from app.application.evaluation_service import EvaluationService
    from app.comparisons.comparator import RegressionThresholds, compare_evaluation_runs
    from app.storage.database import get_session_factory, init_db

    console = Console()
    init_db()
    session_factory = get_session_factory()

    with session_factory() as session:
        service = EvaluationService(session)
        baseline = service.get_run(baseline_run_id)
        if not baseline:
            console.print(f"[bold red]Baseline run '{baseline_run_id}' not found.[/]")
            raise typer.Exit(code=1)

        candidate = service.get_run(candidate_run_id)
        if not candidate:
            console.print(f"[bold red]Candidate run '{candidate_run_id}' not found.[/]")
            raise typer.Exit(code=1)

        base_cases = service.get_run_results(baseline_run_id)
        base_aggs = service.get_run_aggregates(baseline_run_id)
        cand_cases = service.get_run_results(candidate_run_id)
        cand_aggs = service.get_run_aggregates(candidate_run_id)

    if not base_aggs or not cand_aggs:
        console.print("[bold red]Both runs must have aggregate metrics to compare.[/]")
        raise typer.Exit(code=1)

    thresholds = RegressionThresholds(
        max_allowed_pass_rate_drop=max_drop,
        max_allowed_latency_increase_ms=max_latency_increase,
    )

    try:
        cmp = compare_evaluation_runs(
            baseline=baseline,
            baseline_cases=base_cases,
            baseline_aggs=base_aggs,
            candidate=candidate,
            candidate_cases=cand_cases,
            candidate_aggs=cand_aggs,
            thresholds=thresholds,
            allow_different_datasets=allow_different_datasets,
        )
    except Exception as exc:
        console.print(f"[bold red]Comparison error:[/] {exc}")
        raise typer.Exit(code=1) from exc

    status_color = "green" if cmp.passed_regression_gate else "red"
    console.print(f"\n[bold {status_color}]Quality Gate: [{'PASSED' if cmp.passed_regression_gate else 'FAILED'}][/]")
    console.print(cmp.summary)

    if cmp.threshold_violations:
        console.print("\n[bold red]Regression Violations:[/]")
        for v in cmp.threshold_violations:
            console.print(f"  ✘ {v}")

    if cmp.regressed_cases:
        table = Table(title="Regressed Test Cases (Passed -> Failed)")
        table.add_column("Case ID", style="cyan")
        table.add_column("Reason", style="red")
        for r in cmp.regressed_cases:
            table.add_row(r.case_id, r.reason)
        console.print(table)

    if not cmp.passed_regression_gate:
        raise typer.Exit(code=1)


@cli_app.command(name="version")
def version_command() -> None:
    """Print the current EvalForge20 version."""
    typer.echo(f"EvalForge20 version: {__version__}")


if __name__ == "__main__":
    cli_app()
