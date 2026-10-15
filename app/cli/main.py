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


@cli_app.command(name="version")
def version_command() -> None:
    """Print the current EvalForge20 version."""
    typer.echo(f"EvalForge20 version: {__version__}")


if __name__ == "__main__":
    cli_app()
