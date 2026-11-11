import csv
import io
from typing import Any

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.evalforge.core.errors import DataValidationError, NotFoundError
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
        config_snapshot=getattr(run, "config", {}) or {},
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
    sort_by: str = Query(
        "created_at",
        pattern="^(created_at|name|status|model_id|pass_rate|avg_latency_ms)$",
    ),
    sort_order: str = Query("desc", pattern="^(asc|desc)$"),
    db: AsyncSession = Depends(get_db),
) -> EvaluationListResponse:
    """List evaluations filtered by status, model, dataset, or query with stable sorting."""
    service = EvaluationService(db)
    runs, total = await service.list_evaluations(
        status=status_filter,
        model_id=model_id,
        dataset_id=dataset_id,
        query=query,
        offset=offset,
        limit=limit,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    return EvaluationListResponse(
        total=total,
        items=[_map_run_response(r) for r in runs],
    )


@evaluations_router.get(
    "/compare",
    summary="Compare runs and report reproducibility compatibility",
)
async def compare_evaluations(
    ids: list[str] = Query(..., min_length=2, description="Evaluation run IDs to compare"),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Return side-by-side metrics plus an explicit compatibility assessment.

    Runs are only directly comparable when they share the same dataset snapshot,
    evaluator set, and configuration fingerprint. Differences are reported rather
    than silently averaged.
    """
    if len(ids) > 10:
        raise DataValidationError("At most 10 evaluation runs can be compared at once.")

    service = EvaluationService(db)
    runs = []
    for evaluation_id in ids:
        run = await service.get_evaluation(evaluation_id)
        runs.append(run)

    snapshots = [getattr(run, "config", {}) or {} for run in runs]
    reference = snapshots[0]
    reference_dataset = reference.get("dataset", {})
    reference_evaluators = sorted(reference.get("evaluators") or [])
    reference_fingerprint = reference.get("config_fingerprint")

    compatibility = []
    for run, snapshot in zip(runs, snapshots, strict=True):
        reasons = []
        dataset = snapshot.get("dataset", {})
        if dataset.get("snapshot_hash") != reference_dataset.get("snapshot_hash"):
            reasons.append("dataset_snapshot_differs")
        if sorted(snapshot.get("evaluators") or []) != reference_evaluators:
            reasons.append("evaluator_set_differs")
        if snapshot.get("config_fingerprint") != reference_fingerprint:
            reasons.append("configuration_differs")
        compatibility.append(
            {
                "id": run.id,
                "model_id": run.model_id,
                "provider": run.provider,
                "run_fingerprint": snapshot.get("run_fingerprint"),
                "config_fingerprint": snapshot.get("config_fingerprint"),
                "dataset_snapshot_hash": dataset.get("snapshot_hash"),
                "dataset_version": dataset.get("version"),
                "compatible_with_reference": not reasons,
                "differences": reasons,
            }
        )

    metric_names = ["pass_rate", "error_rate", "avg_latency_ms", "median_latency_ms", "p95_latency_ms"]
    metric_comparison = {
        metric: {
            run.id: getattr(run, metric, None)
            for run in runs
        }
        for metric in metric_names
    }
    deltas = {}
    baseline_id, baseline_run = runs[0].id, runs[0]
    for run in runs[1:]:
        deltas[run.id] = {}
        for metric in ("pass_rate", "avg_latency_ms"):
            base_value = getattr(baseline_run, metric, None)
            value = getattr(run, metric, None)
            if base_value is not None and value is not None:
                deltas[run.id][f"{metric}_delta"] = float(value) - float(base_value)

    return {
        "runs": [_map_run_response(run).model_dump() for run in runs],
        "compatibility": compatibility,
        "all_compatible": all(item["compatible_with_reference"] for item in compatibility),
        "metric_comparison": metric_comparison,
        "deltas_from": baseline_id,
        "deltas": deltas,
    }


@evaluations_router.get(
    "/{evaluation_id}",
    summary="Get evaluation status and summary",
)
async def get_evaluation(
    evaluation_id: str,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Fetch current execution status and aggregated metrics scorecard with fallback to execution runs."""
    service = EvaluationService(db)
    try:
        run = await service.get_evaluation(evaluation_id)
        return _map_run_response(run)
    except NotFoundError:
        # Evaluations created through the visual workflow engine are stored as
        # execution runs; fall back only for a genuine 404, never for internal errors.
        from src.evalforge.api.routes.executions import get_execution_results
        return await get_execution_results(execution_id=evaluation_id)


@evaluations_router.get(
    "/{evaluation_id}/results",
    summary="Get evaluation with individual case results",
)
async def get_evaluation_results(
    evaluation_id: str,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Retrieve full audit evidence and individual test case outcomes with fallback to execution runs."""
    service = EvaluationService(db)
    try:
        run = await service.get_evaluation_with_results(evaluation_id)
    except NotFoundError:
        from src.evalforge.api.routes.executions import get_execution_results
        return await get_execution_results(execution_id=evaluation_id)

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

