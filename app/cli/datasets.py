"""CLI commands for dataset validation and inspection."""

from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from app.datasets.hasher import compute_cases_hash
from app.datasets.validator import validate_dataset

dataset_cli = typer.Typer(help="Manage and validate evaluation datasets.")
console = Console()


@dataset_cli.command(name="validate")
def validate_command(
    path: Path = typer.Argument(..., help="Path to JSONL dataset file", exists=True),
) -> None:
    """Validate dataset schema, line-by-line syntax, and check for duplicate IDs."""
    console.print(f"[bold blue]Validating dataset:[/] {path}")
    report = validate_dataset(path)

    if report.is_valid:
        content_hash = compute_cases_hash(report.cases)
        console.print(f"[bold green]✔ Dataset is valid![/] Found {report.valid_cases_count} cases.")
        console.print(f"[dim]SHA-256 Hash:[/] {content_hash}")
        raise typer.Exit(code=0)
    else:
        console.print(
            f"[bold red]✘ Dataset validation failed with {len(report.issues)} issue(s):[/]"
        )
        for issue in report.issues:
            case_info = f" [cyan](id={issue.case_id})[/]" if issue.case_id else ""
            console.print(
                f"  [red]Line {issue.line_number}:[/] [yellow][{issue.error_type}][/]{case_info} {issue.message}"
            )
        raise typer.Exit(code=1)


@dataset_cli.command(name="inspect")
def inspect_command(
    path: Path = typer.Argument(..., help="Path to JSONL dataset file", exists=True),
) -> None:
    """Inspect dataset statistics, category distributions, and metadata."""
    report = validate_dataset(path)
    if not report.is_valid:
        console.print(f"[bold red]Cannot inspect invalid dataset:[/] {path}")
        console.print(report.format_errors())
        raise typer.Exit(code=1)

    content_hash = compute_cases_hash(report.cases)
    stats = report.stats

    table = Table(title=f"Dataset Inspection: {path.name}")
    table.add_column("Property", style="cyan", no_wrap=True)
    table.add_column("Value", style="magenta")

    table.add_row("Total Test Cases", str(stats.total_cases))
    table.add_row("With Expected Output", str(stats.cases_with_expected_output))
    table.add_row("With RAG Context", str(stats.has_context_count))
    table.add_row("With Agent Tools", str(stats.has_tools_count))
    table.add_row("SHA-256 Hash", content_hash)

    console.print(table)

    if stats.categories_distribution:
        cat_table = Table(title="Category Distribution")
        cat_table.add_column("Category", style="green")
        cat_table.add_column("Count", style="yellow")
        for cat, count in sorted(
            stats.categories_distribution.items(), key=lambda x: x[1], reverse=True
        ):
            cat_table.add_row(cat, str(count))
        console.print(cat_table)

    if stats.tags_distribution:
        tag_table = Table(title="Tags Distribution")
        tag_table.add_column("Tag", style="blue")
        tag_table.add_column("Count", style="yellow")
        for tag, count in sorted(stats.tags_distribution.items(), key=lambda x: x[1], reverse=True):
            tag_table.add_row(tag, str(count))
        console.print(tag_table)
