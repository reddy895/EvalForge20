"""CLI commands for exporting evaluation reports in JSON, Markdown, and CSV formats."""

from pathlib import Path

import typer
from rich.console import Console

from app.application.evaluation_service import EvaluationService
from app.reporting.csv_exporter import export_csv_report_to_file, generate_csv_report
from app.reporting.json_exporter import export_report_to_file, generate_json_report
from app.reporting.markdown_exporter import (
    export_markdown_report_to_file,
    generate_markdown_report,
)
from app.storage.database import get_session_factory, init_db

report_cli = typer.Typer(
    help="Export and display evaluation reports in JSON, Markdown, or CSV.",
)
console = Console()


@report_cli.command(name="export")
def export_report_command(
    run_id: str = typer.Argument(..., help="Evaluation run ID to export"),
    format: str = typer.Option(
        "json", "--format", "-f", help="Export format: json, markdown (md), or csv"
    ),
    output: Path | None = typer.Option(None, "--output", "-o", help="Target output file path"),
    redact_inputs: bool = typer.Option(
        False, "--redact-inputs", help="Redact raw inputs/prompts in exported report"
    ),
    redact_outputs: bool = typer.Option(
        False, "--redact-outputs", help="Redact raw model outputs in exported report"
    ),
) -> None:
    """Export evaluation report in JSON, Markdown, or CSV format."""
    fmt = format.lower().strip()
    if fmt not in ("json", "markdown", "md", "csv"):
        console.print(
            f"[bold red]Unsupported report format:[/] '{format}'. Supported formats: ['json', 'markdown', 'csv']"
        )
        raise typer.Exit(code=1)

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
            console.print(f"[bold red]No aggregate metrics found for run '{run_id}'.[/]")
            raise typer.Exit(code=1)

    if fmt == "json":
        report_data = generate_json_report(
            record,
            case_results,
            aggregates,
            redact_inputs=redact_inputs,
            redact_outputs=redact_outputs,
        )
        dest_path = output or Path(f"reports/{run_id}.json")
        saved_path = export_report_to_file(dest_path, report_data)
    elif fmt in ("markdown", "md"):
        md_content = generate_markdown_report(record, case_results, aggregates)
        dest_path = output or Path(f"reports/{run_id}.md")
        saved_path = export_markdown_report_to_file(dest_path, md_content)
    elif fmt == "csv":
        csv_content = generate_csv_report(record, case_results)
        dest_path = output or Path(f"reports/{run_id}.csv")
        saved_path = export_csv_report_to_file(dest_path, csv_content)

    console.print(f"[bold green]✔ Report successfully exported:[/] {saved_path}")
