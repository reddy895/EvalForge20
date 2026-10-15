"""CLI commands for launching evaluations and inspecting run history."""

import asyncio
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from app.application.evaluation_service import EvaluationService
from app.domain.models import EvaluatorConfiguration, TargetConfiguration, TargetType
from app.runner.config import EvaluationRunConfig
from app.storage.database import get_session_factory, init_db

runs_cli = typer.Typer(help="Inspect evaluation runs and history.")
console = Console()


def run_evaluation_cli(
    dataset: Path,
    provider: str = "mock",
    model: str = "mock-model-v1",
    metrics: str = "exact_match,normalized_match",
    concurrency: int = 5,
    retries: int = 2,
    timeout: float = 60.0,
    name: str = "CLI Evaluation Run",
) -> None:
    """Launch an evaluation run from terminal."""
    init_db()
    session_factory = get_session_factory()

    metric_ids = [m.strip() for m in metrics.split(",") if m.strip()]
    evaluators = [EvaluatorConfiguration(evaluator_name=m, metric_id=m) for m in metric_ids]

    target_type = TargetType.OLLAMA if provider.lower() == "ollama" else TargetType.MOCK
    target_cfg = TargetConfiguration(
        target_name=f"{provider}-{model}",
        target_type=target_type,
        provider_name=provider,
        model_identifier=model,
    )

    config = EvaluationRunConfig(
        name=name,
        dataset_path=dataset,
        target=target_cfg,
        evaluators=evaluators,
        max_concurrency=concurrency,
        max_retries=retries,
        timeout_seconds=timeout,
    )

    console.print(f"[bold blue]Starting evaluation run:[/] {config.run_id}")
    console.print(
        f"[dim]Dataset:[/] {dataset} | [dim]Provider:[/] {provider} | [dim]Model:[/] {model}"
    )

    with session_factory() as session:
        service = EvaluationService(session)
        record, results, aggregates = asyncio.run(service.run_evaluation(config))

    status_color = "green" if record.status.value == "completed" else "yellow"
    console.print(f"\n[bold {status_color}]Run Finished:[/] [{record.status.value.upper()}]")

    table = Table(title="Evaluation Summary")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="magenta")

    table.add_row("Run ID", record.run_id)
    table.add_row("Total Cases", str(record.total_cases))
    table.add_row("Completed Cases", str(record.completed_cases))
    table.add_row("Failed Cases", str(record.failed_cases))
    if aggregates.pass_rate is not None:
        table.add_row("Pass Rate", f"{aggregates.pass_rate * 100:.1f}%")
    if aggregates.mean_latency_ms is not None:
        table.add_row("Mean Latency", f"{aggregates.mean_latency_ms:.1f} ms")
    if aggregates.total_tokens is not None:
        table.add_row("Total Tokens", str(aggregates.total_tokens))

    console.print(table)


@runs_cli.command(name="list")
def list_runs_command(limit: int = 20) -> None:
    """List historical evaluation runs."""
    init_db()
    session_factory = get_session_factory()

    with session_factory() as session:
        service = EvaluationService(session)
        runs = service.list_runs(limit=limit)

    table = Table(title=f"Evaluation Runs (Last {limit})")
    table.add_column("Run ID", style="cyan", no_wrap=True)
    table.add_column("Name", style="white")
    table.add_column("Status", style="yellow")
    table.add_column("Cases", style="magenta")
    table.add_column("Started At", style="dim")

    for r in runs:
        started = r.started_at.strftime("%Y-%m-%d %H:%M:%S") if r.started_at else "-"
        table.add_row(
            r.run_id, r.name, r.status.value, f"{r.completed_cases}/{r.total_cases}", started
        )

    console.print(table)


@runs_cli.command(name="show")
def show_run_command(run_id: str) -> None:
    """Inspect detailed results and metrics for a specific evaluation run."""
    init_db()
    session_factory = get_session_factory()

    with session_factory() as session:
        service = EvaluationService(session)
        record = service.get_run(run_id)
        if not record:
            console.print(f"[bold red]Run '{run_id}' not found.[/]")
            raise typer.Exit(code=1)

        aggregates = service.get_run_aggregates(run_id)
        results = service.get_run_results(run_id)

    console.print(f"[bold blue]Run Details:[/] {record.run_id} ({record.name})")
    console.print(
        f"Status: [{record.status.value}] | Total: {record.total_cases} | Completed: {record.completed_cases}"
    )

    if aggregates and aggregates.metric_averages:
        m_table = Table(title="Metric Scores")
        m_table.add_column("Metric ID", style="cyan")
        m_table.add_column("Average Score", style="green")
        m_table.add_column("Pass Rate", style="yellow")
        for mid, avg in aggregates.metric_averages.items():
            pr = aggregates.metric_pass_rates.get(mid)
            pr_str = f"{pr * 100:.1f}%" if pr is not None else "N/A"
            m_table.add_row(mid, f"{avg:.3f}", pr_str)
        console.print(m_table)

    c_table = Table(title=f"Case Results ({len(results)} cases)")
    c_table.add_column("Case ID", style="cyan")
    c_table.add_column("Output Preview", style="white")
    c_table.add_column("Latency", style="dim")
    c_table.add_column("Status", style="yellow")

    for c in results[:10]:
        out = str(c.actual_output)[:40] if c.actual_output else "[Error]"
        lat = f"{c.latency_ms:.0f}ms" if c.latency_ms else "-"
        stat = "[red]FAIL" if c.error_category else "[green]PASS"
        c_table.add_row(c.case_id, out, lat, stat)

    console.print(c_table)
    if len(results) > 10:
        console.print(f"[dim]...showing first 10 of {len(results)} cases[/]")
