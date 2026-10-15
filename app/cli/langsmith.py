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
