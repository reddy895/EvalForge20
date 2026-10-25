import csv
import io
from typing import Any

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.evalforge.schemas.evaluation import (
    CaseResultResponse,
    EvaluationCreateRequest,
    EvaluationDetailResponse,
    EvaluationListResponse,
    EvaluationResponse,
)
from src.evalforge.services.evaluation_service import EvaluationService
from src.evalforge.storage.database import get_db

evaluations_router = APIRouter(prefix="/evaluations", tags=["Evaluations"])


def _map_run_response(run: object) -> EvaluationResponse:
    """Helper formatting EvaluationRun model to EvaluationResponse schema."""
    summary = getattr(run, "summary_metrics", {}) or {}
    return EvaluationResponse(
        id=run.id,  # type: ignore[attr-defined]
        name=run.name,  # type: ignore[attr-defined]
        model_id=run.model_id,  # type: ignore[attr-defined]
        provider=run.provider,  # type: ignore[attr-defined]
        dataset_id=run.dataset_id,  # type: ignore[attr-defined]
        dataset_name=run.dataset_name,  # type: ignore[attr-defined]
        status=run.status,  # type: ignore[attr-defined]
        total_cases=run.total_cases,  # type: ignore[attr-defined]
        completed_cases=run.completed_cases,  # type: ignore[attr-defined]
        passed_cases=run.passed_cases,  # type: ignore[attr-defined]
        failed_cases=run.failed_cases,  # type: ignore[attr-defined]
        pass_rate=run.pass_rate,  # type: ignore[attr-defined]
        error_rate=summary.get("error_rate"),
        avg_latency_ms=run.avg_latency_ms,  # type: ignore[attr-defined]
        median_latency_ms=summary.get("p50_latency_ms") or summary.get("median_latency_ms"),
        p95_latency_ms=summary.get("p95_latency_ms"),
        tokens_per_second=summary.get("avg_tokens_per_second") or summary.get("avg_throughput_tok_s"),
        load_duration_ms=summary.get("avg_load_duration_ms"),
        summary_metrics=summary,
        error_message=run.error_message,  # type: ignore[attr-defined]
        created_at=(
            run.created_at.isoformat()  # type: ignore[attr-defined]
            if hasattr(run.created_at, "isoformat")  # type: ignore[attr-defined]
            else str(run.created_at or "")  # type: ignore[attr-defined]
        ),
        completed_at=(
            run.completed_at.isoformat()  # type: ignore[attr-defined]
            if run.completed_at and hasattr(run.completed_at, "isoformat")  # type: ignore[attr-defined]
            else (str(run.completed_at) if run.completed_at else None)  # type: ignore[attr-defined]
        ),
    )


@evaluations_router.post(
    "",
    response_model=EvaluationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create and start an evaluation run",
)
async def create_evaluation(
    payload: EvaluationCreateRequest,
    db: AsyncSession = Depends(get_db),
) -> EvaluationResponse:
    """Queue and execute an evaluation run over a dataset with bounded concurrency."""
    service = EvaluationService(db)
    run = await service.create_and_start_run(payload)
    return _map_run_response(run)


@evaluations_router.get(
    "",
    response_model=EvaluationListResponse,
    summary="List evaluation runs",
)
async def list_evaluations(
    status_filter: str | None = Query(None, alias="status"),
    model_id: str | None = Query(None),
    dataset_id: str | None = Query(None),
    query: str | None = Query(None),
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> EvaluationListResponse:
    """List evaluations filtered by status, target model, source dataset, or search query."""
    service = EvaluationService(db)
    runs, total = await service.list_evaluations(
        status=status_filter,
        model_id=model_id,
        dataset_id=dataset_id,
        query=query,
        offset=offset,
        limit=limit,
    )
    return EvaluationListResponse(
        total=total,
        items=[_map_run_response(r) for r in runs],
    )


@evaluations_router.get(
    "/{evaluation_id}",
    response_model=EvaluationResponse,
    summary="Get evaluation status and summary",
)
async def get_evaluation(
    evaluation_id: str,
    db: AsyncSession = Depends(get_db),
) -> EvaluationResponse:
    """Fetch current execution status and aggregated metrics scorecard."""
    service = EvaluationService(db)
    run = await service.get_evaluation(evaluation_id)
    return _map_run_response(run)


@evaluations_router.get(
    "/{evaluation_id}/results",
    response_model=EvaluationDetailResponse,
    summary="Get evaluation with individual case results",
)
async def get_evaluation_results(
    evaluation_id: str,
    db: AsyncSession = Depends(get_db),
) -> EvaluationDetailResponse:
    """Retrieve full audit evidence and individual test case outcomes."""
    service = EvaluationService(db)
    run = await service.get_evaluation_with_results(evaluation_id)
    base_resp = _map_run_response(run)

    case_items = []
    for c in run.results:
        m_dict = c.metrics or {}
        u_dict = c.token_usage or {}
        ass_type = m_dict.get("_assertion_type") or u_dict.get("assertion_type") or "exact_match"
        tps = u_dict.get("tokens_per_second") or m_dict.get("_tokens_per_second")
        load_ms = u_dict.get("load_duration_ms") or m_dict.get("_load_duration_ms")
        case_latency = (
            c.latency_ms
            if (c.latency_ms is not None and c.latency_ms > 0 and not c.error_message)
            else None
        )
        case_items.append(
            CaseResultResponse(
                id=c.id,
                case_id=c.case_id,
                prompt=c.prompt,
                expected_output=c.expected_output,
                actual_output=c.actual_output,
                passed=c.passed,
                latency_ms=case_latency,
                assertion_type=ass_type,
                tokens_per_second=tps,
                load_duration_ms=load_ms,
                metrics=m_dict,
                token_usage=u_dict,
                error_message=c.error_message,
                created_at=(
                    c.created_at.isoformat()
                    if hasattr(c.created_at, "isoformat")
                    else str(c.created_at or "")
                ),
            )
        )

    return EvaluationDetailResponse(
        **base_resp.model_dump(),
        results=case_items,
        case_results=case_items,
    )


@evaluations_router.post(
    "/{evaluation_id}/cancel",
    response_model=EvaluationResponse,
    summary="Cancel an active evaluation run",
)
async def cancel_evaluation(
    evaluation_id: str,
    db: AsyncSession = Depends(get_db),
) -> EvaluationResponse:
    """Signal cooperative cancellation to abort an active evaluation."""
    service = EvaluationService(db)
    run = await service.cancel_evaluation(evaluation_id)
    return _map_run_response(run)


@evaluations_router.get(
    "/{evaluation_id}/export",
    summary="Export evaluation run results in JSON or CSV format",
)
async def export_evaluation(
    evaluation_id: str,
    format: str = Query("json", pattern="^(json|csv)$"),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Export the evaluation run and all case results for reproducibility and offline audit."""
    service = EvaluationService(db)
    run = await service.get_evaluation_with_results(evaluation_id)

    if format == "csv":
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            "case_id",
            "passed",
            "latency_ms",
            "tokens_per_second",
            "prompt",
            "expected_output",
            "actual_output",
            "error_message",
        ])
        for c in run.results:
            u_dict = c.token_usage or {}
            m_dict = c.metrics or {}
            tps = u_dict.get("tokens_per_second") or m_dict.get("_tokens_per_second") or ""
            writer.writerow([
                c.case_id,
                c.passed,
                c.latency_ms,
                tps,
                c.prompt,
                c.expected_output or "",
                c.actual_output or "",
                c.error_message or "",
            ])
        csv_data = output.getvalue()
        return Response(
            content=csv_data,
            media_type="text/csv",
            headers={"Content-Disposition": f'attachment; filename="eval_{evaluation_id}.csv"'},
        )

    # JSON reproducible format
    return await get_evaluation_results(evaluation_id=evaluation_id, db=db)

