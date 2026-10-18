"""Evaluation run creation, status inspection, and report export API routes."""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session

from app.api.schemas import CreateEvaluationRequest, RunSummaryResponse
from app.application.evaluation_service import EvaluationService
from app.datasets.validator import validate_dataset
from app.domain.results import CaseResult
from app.reporting.csv_exporter import generate_csv_report
from app.reporting.json_exporter import generate_json_report
from app.reporting.markdown_exporter import generate_markdown_report
from app.runner.config import EvaluationRunConfig
from app.storage.database import get_db

eval_router = APIRouter(tags=["Evaluations"])


@eval_router.post(
    "/v1/evaluations",
    response_model=RunSummaryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create and execute an evaluation run",
)
async def create_evaluation_endpoint(
    req: CreateEvaluationRequest,
    db: Session = Depends(get_db),
) -> RunSummaryResponse:
    """Launch an evaluation run against configured target and evaluators."""
    service = EvaluationService(db)

    # Resolve dataset cases if supplied inline
    cases_override = None
    if req.dataset_content:
        report = validate_dataset(req.dataset_content)
        if not report.is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid dataset content: {report.format_errors()}",
            )
        cases_override = report.cases

    config = EvaluationRunConfig(
        name=req.name,
        dataset_path=req.dataset_path,
        target=req.target,
        evaluators=req.evaluators,
        max_concurrency=req.max_concurrency,
        max_retries=req.max_retries,
        timeout_seconds=req.timeout_seconds,
    )

    try:
        record, results, aggregates = await service.run_evaluation(
            config, cases_override=cases_override
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to execute evaluation: {exc}",
        ) from exc

    return RunSummaryResponse(
        run_id=record.run_id,
        name=record.name,
        status=record.status.value,
        total_cases=record.total_cases,
        completed_cases=record.completed_cases,
        failed_cases=record.failed_cases,
        started_at=record.started_at.isoformat() if record.started_at else None,
        completed_at=record.completed_at.isoformat() if record.completed_at else None,
        pass_rate=aggregates.pass_rate,
        error_message=record.error_message,
        model_identifier=record.config.target.model_identifier,
        provider_name=record.config.target.provider_name,
        mean_latency_ms=aggregates.mean_latency_ms,
        total_tokens=aggregates.total_tokens,
    )


@eval_router.get(
    "/v1/evaluations",
    response_model=list[RunSummaryResponse],
    summary="List historical evaluation runs",
)
async def list_evaluations_endpoint(
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    status: str | None = Query(default=None, description="Filter by execution status"),
    model_identifier: str | None = Query(default=None, description="Filter by target model"),
    min_pass_rate: float | None = Query(
        default=None, ge=0.0, le=1.0, description="Filter by minimum pass rate"
    ),
    db: Session = Depends(get_db),
) -> list[RunSummaryResponse]:
    """Retrieve paginated list of evaluation runs with optional filters."""
    service = EvaluationService(db)
    runs = service.list_runs(
        limit=limit,
        offset=offset,
        status=status,
        model_identifier=model_identifier,
        min_pass_rate=min_pass_rate,
    )

    summaries = []
    for r in runs:
        aggs = service.get_run_aggregates(r.run_id)
        summaries.append(
            RunSummaryResponse(
                run_id=r.run_id,
                name=r.name,
                status=r.status.value,
                total_cases=r.total_cases,
                completed_cases=r.completed_cases,
                failed_cases=r.failed_cases,
                started_at=r.started_at.isoformat() if r.started_at else None,
                completed_at=r.completed_at.isoformat() if r.completed_at else None,
                pass_rate=aggs.pass_rate if aggs else None,
                error_message=r.error_message,
                model_identifier=r.config.target.model_identifier,
                provider_name=r.config.target.provider_name,
                mean_latency_ms=aggs.mean_latency_ms if aggs else None,
                total_tokens=aggs.total_tokens if aggs else None,
            )
        )
    return summaries


@eval_router.get(
    "/v1/evaluations/{run_id}",
    summary="Retrieve evaluation run status and aggregate metrics",
)
async def get_evaluation_endpoint(
    run_id: str,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Retrieve run record details and dataset-level aggregate metrics."""
    service = EvaluationService(db)
    record = service.get_run(run_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Evaluation run '{run_id}' not found",
        )

    aggregates = service.get_run_aggregates(run_id)
    return {
        "run": record.model_dump(),
        "aggregates": aggregates.model_dump() if aggregates else None,
    }


@eval_router.get(
    "/v1/evaluations/{run_id}/results",
    response_model=list[CaseResult],
    summary="Retrieve per-case results for an evaluation run",
)
async def get_case_results_endpoint(
    run_id: str,
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> list[CaseResult]:
    """Retrieve paginated case-level outputs, scores, and execution metadata."""
    service = EvaluationService(db)
    record = service.get_run(run_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Evaluation run '{run_id}' not found",
        )

    all_results = service.get_run_results(run_id)
    return all_results[offset : offset + limit]


@eval_router.get(
    "/v1/evaluations/{run_id}/failures",
    response_model=list[CaseResult],
    summary="Retrieve failed and errored cases for an evaluation run",
)
async def get_failed_cases_endpoint(
    run_id: str,
    db: Session = Depends(get_db),
) -> list[CaseResult]:
    """Retrieve only test cases that failed assertion checks or encountered errors."""
    service = EvaluationService(db)
    record = service.get_run(run_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Evaluation run '{run_id}' not found",
        )
    return service.repo.get_run_failure_cases(run_id)


@eval_router.delete(
    "/v1/evaluations/{run_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete an evaluation run and its results",
)
async def delete_evaluation_endpoint(
    run_id: str,
    db: Session = Depends(get_db),
) -> dict[str, str]:
    """Permanently delete an evaluation run and associated case results."""
    service = EvaluationService(db)
    deleted = service.repo.delete_run(run_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Evaluation run '{run_id}' not found",
        )
    return {"message": f"Evaluation run '{run_id}' deleted successfully"}


@eval_router.get(
    "/v1/reports/{run_id}",
    summary="Generate and export evaluation report in JSON, Markdown, or CSV format",
)
async def get_report_endpoint(
    run_id: str,
    format: str = Query(
        default="json",
        description="Desired export format ('json', 'markdown'/'md', or 'csv')",
    ),
    redact_inputs: bool = Query(
        default=False, description="Redact raw inputs/prompts in exported report"
    ),
    redact_outputs: bool = Query(
        default=False, description="Redact raw model outputs in exported report"
    ),
    db: Session = Depends(get_db),
) -> Any:
    """Return complete evaluation report in requested format (JSON, Markdown, or CSV)."""
    service = EvaluationService(db)
    record = service.get_run(run_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Evaluation run '{run_id}' not found",
        )

    case_results = service.get_run_results(run_id)
    aggregates = service.get_run_aggregates(run_id)
    if not aggregates:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Run '{run_id}' has no aggregate metrics computed yet",
        )

    fmt = format.strip().lower()
    if fmt == "json":
        return generate_json_report(
            record,
            case_results,
            aggregates,
            redact_inputs=redact_inputs,
            redact_outputs=redact_outputs,
        )
    elif fmt in ("markdown", "md"):
        content = generate_markdown_report(record, case_results, aggregates)
        return PlainTextResponse(content, media_type="text/markdown")
    elif fmt == "csv":
        content = generate_csv_report(record, case_results)
        return PlainTextResponse(content, media_type="text/csv")
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported report format '{format}'. Supported formats: ['json', 'markdown', 'csv']",
        )
