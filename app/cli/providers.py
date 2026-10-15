"""CLI commands for inspecting and checking model providers."""

import asyncio
import typer
from rich.console import Console
from rich.table import Table

from app.providers.registry import provider_registry

provider_cli = typer.Typer(help="Inspect and health-check model providers.")
console = Console()


@provider_cli.command(name="list")
def list_providers_command() -> None:
    """List all configured model providers."""
    providers = provider_registry.list_providers()
    table = Table(title="Configured Providers")
    table.add_column("Provider Name", style="cyan")
    for p in providers:
        table.add_row(p)
    console.print(table)


@provider_cli.command(name="check")
def check_provider_command(
    provider_name: str = typer.Argument(..., help="Name of provider to check (e.g. ollama, mock)"),
) -> None:
    """Check connectivity and health of a specific provider."""
    console.print(f"[bold blue]Checking provider:[/] {provider_name}")
    try:
        prov = provider_registry.get(provider_name)
    except Exception as exc:
        console.print(f"[bold red]✘ Provider '{provider_name}' not found:[/] {exc}")
        raise typer.Exit(code=1) from exc

    is_healthy = asyncio.run(prov.health_check())
    if is_healthy:
        models = asyncio.run(prov.list_models())
        console.print(f"[bold green]✔ Provider '{provider_name}' is healthy and available.[/]")
        if models:
            console.print(f"[dim]Available models:[/] {', '.join(models[:10])}")
        raise typer.Exit(code=0)
    else:
        console.print(f"[bold red]✘ Provider '{provider_name}' is unreachable or failed health check.[/]")
        raise typer.Exit(code=1)
