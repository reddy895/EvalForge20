"""CLI commands for managing LangSmith integration."""

import asyncio
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from app.integrations.langsmith.client import check_langsmith_connection

langsmith_cli = typer.Typer(help="Manage and diagnose LangSmith integration.")
console = Console()


@langsmith_cli.command(name="status")
def status_command() -> None:
    """Display LangSmith configuration and connectivity diagnostics."""
    status_info = asyncio.run(check_langsmith_connection())

    status_color = "green" if status_info.connection_status == "reachable" else "yellow"
    table = Table(title="LangSmith Integration Status")
    table.add_column("Property", style="cyan")
    table.add_column("Value", style=status_color)

    table.add_row("Enabled", str(status_info.is_enabled))
    table.add_row("API Key Configured", str(status_info.has_api_key))
    table.add_row("Endpoint", status_info.endpoint)
    table.add_row("Project", status_info.project)
    table.add_row("Auto-Sync Datasets", str(status_info.auto_sync_datasets))
    table.add_row("Connection Status", status_info.connection_status.upper())

    if status_info.error_message:
        table.add_row("Diagnostic Error", status_info.error_message)

    console.print(table)


@langsmith_cli.command(name="sync-dataset")
def sync_dataset_command(
    path: Path = typer.Argument(
        ..., help="Path to JSONL dataset to upload to LangSmith", exists=True
    ),
    name: str | None = typer.Option(None, "--name", "-n", help="Dataset name in LangSmith"),
) -> None:
    """Upload and synchronize an EvalForge20 dataset with LangSmith."""
    from app.datasets.validator import validate_dataset
    from app.integrations.langsmith.dataset_sync import sync_dataset_to_langsmith

    report = validate_dataset(path)
    if not report.is_valid:
        console.print(f"[bold red]Cannot sync invalid dataset:[/] {path}")
        console.print(report.format_errors())
        raise typer.Exit(code=1)

    ds_name = name or path.stem
    try:
        res = sync_dataset_to_langsmith(report.cases, dataset_name=ds_name)
        console.print("[bold green]✔ Successfully synchronized dataset to LangSmith![/]")
        console.print(f"  LangSmith Dataset ID: [cyan]{res['dataset_id']}[/]")
        console.print(f"  Examples Synced: [magenta]{res['synced_examples']}[/]")
    except Exception as exc:
        console.print(f"[bold red]✘ Synchronization failed:[/] {exc}")
        raise typer.Exit(code=1) from exc


@langsmith_cli.command(name="sync-run")
def sync_run_command(
    run_id: str = typer.Argument(..., help="Evaluation run ID to publish to LangSmith"),
) -> None:
    """Publish an existing evaluation run and case scores to LangSmith."""
    from app.application.evaluation_service import EvaluationService
    from app.integrations.langsmith.experiments import sync_run_to_langsmith
    from app.storage.database import get_session_factory, init_db

    init_db()
    session_factory = get_session_factory()

    with session_factory() as session:
        service = EvaluationService(session)
        record = service.get_run(run_id)
        if not record:
            console.print(f"[bold red]Run '{run_id}' not found.[/]")
            raise typer.Exit(code=1)

        case_results = service.get_run_results(run_id)
        aggregates = service.get_run_aggregates(run_id)
        if not aggregates:
            console.print(f"[bold red]Run '{run_id}' has no aggregate metrics.[/]")
            raise typer.Exit(code=1)

    res = sync_run_to_langsmith(record, case_results, aggregates)
    if res.get("status") == "success":
        console.print("[bold green]✔ Successfully published run to LangSmith![/]")
        console.print(f"  LangSmith Run ID: [cyan]{res['langsmith_run_id']}[/]")
        console.print(f"  Project: [magenta]{res['project_name']}[/]")
    elif res.get("status") == "skipped":
        console.print(f"[yellow]⚠ Skipped:[/] {res['reason']}")
    else:
        console.print(f"[bold red]✘ Publishing failed:[/] {res.get('error')}")
        raise typer.Exit(code=1)
