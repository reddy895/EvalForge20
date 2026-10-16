"""CLI commands for discovering and inspecting local models."""

import asyncio

import typer
from rich.console import Console
from rich.table import Table

from app.config import get_settings
from app.providers.ollama import OllamaProvider
from app.providers.ollama_diagnostics import diagnose_ollama

models_cli = typer.Typer(
    name="models",
    help="Discover, inspect, and check models installed locally on Ollama.",
    invoke_without_command=True,
)
console = Console()


@models_cli.callback(invoke_without_command=True)
def list_models_callback(ctx: typer.Context) -> None:
    """List locally available models when 'models' is invoked without sub-commands."""
    if ctx.invoked_subcommand is None:
        list_models_command()


@models_cli.command(name="list")
def list_models_command() -> None:
    """List all locally available LLM models from Ollama."""
    settings = get_settings()
    diag = asyncio.run(diagnose_ollama(base_url=settings.ollama_base_url))

    if not diag.is_reachable:
        console.print(
            f"[bold red]✘ Ollama server is unreachable at {settings.ollama_base_url}.[/]\n"
        )
        console.print("[bold yellow]Setup Instructions:[/]")
        for step in diag.setup_instructions:
            console.print(f"  {step}")
        raise typer.Exit(code=1)

    provider = OllamaProvider(base_url=settings.ollama_base_url)
    detailed_models = asyncio.run(provider.list_detailed_models())

    if not detailed_models:
        console.print(
            f"[bold yellow]No models found installed on Ollama ({settings.ollama_base_url}).[/]\n"
        )
        console.print("To pull a model, run:")
        console.print(f"  ollama pull {settings.ollama_model}")
        return

    table = Table(title=f"Locally Installed Models ({settings.ollama_base_url})")
    table.add_column("Model Name", style="bold cyan")
    table.add_column("Parameters", style="green")
    table.add_column("Quantization", style="magenta")
    table.add_column("Size", style="yellow")
    table.add_column("Modified", style="dim")

    for m in detailed_models:
        size_mb = (
            f"{m.get('size_bytes', 0) / (1024 * 1024):.1f} MB" if m.get("size_bytes") else "N/A"
        )
        mod_date = str(m.get("modified_at", "N/A"))[:19].replace("T", " ")
        table.add_row(
            m.get("name", "unknown"),
            m.get("parameter_size") or "N/A",
            m.get("quantization_level") or "N/A",
            size_mb,
            mod_date,
        )

    console.print(table)


@models_cli.command(name="check")
def check_model_command(
    model_name: str = typer.Argument(..., help="Model identifier to check (e.g. qwen2.5:3b)"),
) -> None:
    """Verify if a specific model is downloaded and ready for local evaluation."""
    settings = get_settings()
    diag = asyncio.run(diagnose_ollama(base_url=settings.ollama_base_url))

    if not diag.is_reachable:
        console.print(f"[bold red]✘ Ollama daemon unreachable at {settings.ollama_base_url}.[/]")
        raise typer.Exit(code=1)

    # Check model presence (matching with or without tag)
    installed = diag.installed_models
    match = any(
        m == model_name or m.startswith(f"{model_name}:") or model_name.startswith(f"{m}:")
        for m in installed
    )

    if match:
        console.print(f"[bold green]✔ Model '{model_name}' is locally installed and ready.[/]")
    else:
        console.print(f"[bold red]✘ Model '{model_name}' is not found locally.[/]")
        console.print(
            f"[bold yellow]Run this command to pull the model:[/] ollama pull {model_name}"
        )
        raise typer.Exit(code=1)
