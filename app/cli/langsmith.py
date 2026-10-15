"""CLI commands for managing LangSmith integration."""

import asyncio
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
    path: Path = typer.Argument(..., help="Path to JSONL dataset to upload to LangSmith", exists=True),
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
        console.print(f"[bold green]✔ Successfully synchronized dataset to LangSmith![/]")
        console.print(f"  LangSmith Dataset ID: [cyan]{res['dataset_id']}[/]")
        console.print(f"  Examples Synced: [magenta]{res['synced_examples']}[/]")
    except Exception as exc:
        console.print(f"[bold red]✘ Synchronization failed:[/] {exc}")
        raise typer.Exit(code=1) from exc
