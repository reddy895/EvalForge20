"""Main entrypoint for the EvalForge20 command line interface."""

import typer
from app import __version__
from app.cli.datasets import dataset_cli

cli_app = typer.Typer(
    name="evalforge20",
    help="EvalForge20: Production-minded, local-first LLM & AI agent evaluation platform.",
    add_completion=False,
)

# Register sub-commands
cli_app.add_typer(dataset_cli, name="dataset")


@cli_app.command(name="version")
def version_command() -> None:
    """Print the current EvalForge20 version."""
    typer.echo(f"EvalForge20 version: {__version__}")


if __name__ == "__main__":
    cli_app()
