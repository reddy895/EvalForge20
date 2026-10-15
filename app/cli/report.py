"""CLI command for exporting structured JSON evaluation reports."""

from pathlib import Path
import typer
from rich.console import Console

from app.application.evaluation_service import EvaluationService
from app.reporting.json_exporter import export_report_to_file, generate_json_report
from app.storage.database import get_session_factory, init_db

report_cli = typer.Typer(help="Export and manage evaluation reports.")
console = Console()


@report_cli.command(name="export")
def export_report_command(
    run_id: str = typer.Argument(..., help="Evaluation run ID to export"),
    format: str = typer.Option("json", "--format", "-f", help="Export format (json)"),
    output: Path | None = typer.Option(None, "--output", "-o", help="Target output file path"),
) -> None:
    """Export structured JSON report for an evaluation run."""
    if format.lower() != "json":
        console.print(f"[bold red]Unsupported report format:[/] {format}. Only 'json' is currently supported.")
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

    report_data = generate_json_report(record, case_results, aggregates)
    dest_path = output or Path(f"reports/{run_id}.json")
    saved_path = export_report_to_file(dest_path, report_data)

    console.print(f"[bold green]✔ Report successfully exported:[/] {saved_path}")
