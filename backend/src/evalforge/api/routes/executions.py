"""Modular API routes for workflow execution triggers, SSE streaming, and cancellation."""

import json
import uuid
from typing import Any

from fastapi import APIRouter, BackgroundTasks, HTTPException
from fastapi.responses import StreamingResponse

from src.evalforge.core.logging import get_logger
from src.evalforge.database.models import ExecutionRecord, ExperimentRecord, WorkflowRecord
from src.evalforge.database.session import get_db_context
from src.evalforge.engine.events import get_event_broadcaster
from src.evalforge.engine.executor import get_workflow_executor
from src.evalforge.engine.scheduler import get_workflow_scheduler
from src.evalforge.schemas.main import ExecutionTriggerRequest, WorkflowGraph
from src.evalforge.storage.models.evaluation import EvaluationRun

logger = get_logger("evalforge.api.routes.executions")

router = APIRouter(prefix="/executions", tags=["executions"])


@router.post("")
async def trigger_execution(
    payload: ExecutionTriggerRequest, background_tasks: BackgroundTasks
) -> dict[str, Any]:
    executor = get_workflow_executor()
    exec_id = str(uuid.uuid4())
    graph = payload.graph

    if not graph and payload.workflow_id:
        async with get_db_context() as session:
            wf = await session.get(WorkflowRecord, payload.workflow_id)
            if not wf:
                raise HTTPException(status_code=404, detail=f"Workflow '{payload.workflow_id}' not found.")
            graph = WorkflowGraph(**json.loads(wf.graph_json))

    if not graph:
        raise HTTPException(status_code=400, detail="Must provide either 'graph' or valid 'workflow_id'.")

    # Ensure ExecutionRecord is recorded in DB for persistence
    try:
        async with get_db_context() as session:
            rec = ExecutionRecord(
                id=exec_id,
                workflow_id=payload.workflow_id,
                status="RUNNING",
                total_steps=0,
                completed_steps=0,
                logs_json=json.dumps([f"Triggered workflow execution '{payload.execution_name or 'Evaluation Workflow'}'."]),
            )
            session.add(rec)
            await session.commit()
    except Exception as exc:
        logger.warning("Could not persist initial ExecutionRecord: %s", exc)

    # Launch execution as an async background task
    async def _run_job():
        await executor.execute_workflow(
            graph=graph,
            execution_id=exec_id,
            workflow_id=payload.workflow_id,
            name=payload.execution_name,
            judge_model_identifier=payload.judge_model_identifier,
        )

    background_tasks.add_task(_run_job)

    return {
        "execution_id": exec_id,
        "status": "PENDING",
        "message": "Workflow evaluation triggered successfully.",
    }


@router.get("/{execution_id}")
async def get_execution_status(execution_id: str) -> dict[str, Any]:
    broadcaster = get_event_broadcaster()
    events = broadcaster._history.get(execution_id, [])

    status = "PENDING"
    completed = 0
    total = 0
    err = None

    if events:
        last = events[-1]
        completed = last.completed_steps
        total = last.total_steps
        if last.event_type == "completed":
            status = "COMPLETED"
        elif last.event_type == "failed":
            status = "FAILED"
            err = last.message
        elif last.event_type == "cancelled":
            status = "CANCELLED"
        else:
            status = "RUNNING"
    else:
        try:
            async with get_db_context() as session:
                rec = await session.get(ExecutionRecord, execution_id)
                if rec:
                    status = rec.status
                    completed = rec.completed_steps
                    total = rec.total_steps
                    err = rec.error_message
        except Exception:
            pass

    return {
        "id": execution_id,
        "status": status,
        "completed_steps": completed,
        "total_steps": total,
        "error_message": err,
        "events_count": len(events),
    }


@router.get("/{execution_id}/events")
async def stream_execution_events(execution_id: str) -> StreamingResponse:
    broadcaster = get_event_broadcaster()
    return StreamingResponse(
        broadcaster.stream_events(execution_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/{execution_id}/results")
async def get_execution_results(execution_id: str) -> dict[str, Any]:
    """Retrieve comprehensive graphical results and individual test cases for an execution run."""
    from sqlalchemy import select

    # 1. Query ExperimentRecords for this execution_id
    async with get_db_context() as session:
        stmt = (
            select(ExperimentRecord)
            .where(ExperimentRecord.execution_id == execution_id)
            .order_by(ExperimentRecord.created_at)
        )
        res = await session.execute(stmt)
        experiments = list(res.scalars().all())

        exec_rec = await session.get(ExecutionRecord, execution_id)

    # 2. If no experiments in DB, check in-memory broadcaster history for live or recent execution
    broadcaster = get_event_broadcaster()
    events = broadcaster._history.get(execution_id, [])

    if not experiments and events:
        # Reconstruct live progress/results from broadcast events
        last_event = events[-1]
        status = "COMPLETED" if last_event.event_type == "completed" else (
            "FAILED" if last_event.event_type == "failed" else (
                "CANCELLED" if last_event.event_type == "cancelled" else "RUNNING"
            )
        )
        models_seen: set[str] = set()
        cases_by_model: dict[str, list[dict[str, Any]]] = {}
        for ev in events:
            if ev.event_type == "step_progress" and ev.data:
                m_id = ev.data.get("model") or "unknown_model"
                models_seen.add(m_id)
                if "case" in ev.data:
                    case_data = dict(ev.data["case"])
                    case_data["model_id"] = m_id
                    cases_by_model.setdefault(m_id, []).append(case_data)

        model_summaries = []
        all_cases = []
        for m_id in sorted(models_seen):
            m_cases = cases_by_model.get(m_id, [])
            all_cases.extend(m_cases)
            tot = len(m_cases)
            passed = sum(1 for c in m_cases if c.get("passed"))
            failed = tot - passed
            latencies = [c.get("latency_ms") for c in m_cases if c.get("latency_ms") is not None]
            avg_lat = round(sum(latencies) / len(latencies), 2) if latencies else None

            model_summaries.append({
                "model_id": m_id,
                "name": m_id,
                "total_cases": tot,
                "completed_cases": tot,
                "passed_cases": passed,
                "failed_cases": failed,
                "pass_rate": round((passed / tot) * 100, 2) if tot > 0 else 0.0,
                "avg_latency_ms": avg_lat,
                "tokens_per_second": None,
                "status": status,
                "metrics": {},
            })

        total_cases_count = sum(s["total_cases"] for s in model_summaries)
        passed_cases_count = sum(s["passed_cases"] for s in model_summaries)
        failed_cases_count = sum(s["failed_cases"] for s in model_summaries)

        valid_lats = [s["avg_latency_ms"] for s in model_summaries if s["avg_latency_ms"] is not None]
        overall_live_lat = round(sum(valid_lats) / len(valid_lats), 2) if valid_lats else None

        return {
            "id": execution_id,
            "execution_id": execution_id,
            "name": "Live Workflow Execution",
            "status": status,
            "dataset_name": "Active Canvas Workflow",
            "models": sorted(list(models_seen)),
            "evaluators": [],
            "total_cases": total_cases_count,
            "completed_cases": total_cases_count,
            "passed_cases": passed_cases_count,
            "failed_cases": failed_cases_count,
            "pass_rate": round((passed_cases_count / total_cases_count) * 100, 2) if total_cases_count > 0 else 0.0,
            "avg_latency_ms": overall_live_lat,
            "total_duration_ms": None,
            "created_at": exec_rec.started_at.isoformat() if exec_rec and exec_rec.started_at else None,
            "completed_at": exec_rec.completed_at.isoformat() if exec_rec and exec_rec.completed_at else None,
            "model_summaries": model_summaries,
            "case_results": all_cases,
            "disagreements": [],
            "distribution": {
                "passed": passed_cases_count,
                "failed": failed_cases_count,
                "skipped": 0,
            },
        }

    # 3. If no experiments for execution_id, check if execution_id is an EvaluationRun ID
    if not experiments:
        async with get_db_context() as session:
            eval_run = await session.get(EvaluationRun, execution_id)
            if eval_run:
                # Load with case results
                from src.evalforge.storage.repositories.evaluation_repo import EvaluationRepository
                repo = EvaluationRepository(session)
                full_run = await repo.get_with_results(execution_id)
                if full_run:
                    c_items = []
                    for c in full_run.results:
                        m_dict = c.metrics or {}
                        u_dict = c.token_usage or {}
                        tps = u_dict.get("tokens_per_second") or m_dict.get("_tokens_per_second")
                        c_items.append({
                            "case_id": c.case_id,
                            "model_id": full_run.model_id,
                            "prompt": c.prompt,
                            "expected_output": c.expected_output,
                            "actual_output": c.actual_output,
                            "passed": c.passed,
                            "latency_ms": c.latency_ms,
                            "tokens_per_second": tps,
                            "assertion_type": m_dict.get("_assertion_type") or "exact_match",
                            "metrics": m_dict,
                            "token_usage": u_dict,
                            "error_message": c.error_message,
                            "created_at": c.created_at.isoformat() if hasattr(c.created_at, "isoformat") else str(c.created_at or ""),
                        })

                    summary_metrics = full_run.summary_metrics or {}
                    tps_overall = summary_metrics.get("avg_tokens_per_second") or summary_metrics.get("avg_throughput_tok_s")
                    exact_match_score = summary_metrics.get("metric_averages", {}).get("exact_match")
                    if exact_match_score is None and full_run.pass_rate is not None:
                        exact_match_score = full_run.pass_rate

                    model_summary = {
                        "model_id": full_run.model_id,
                        "name": full_run.model_id,
                        "total_cases": full_run.total_cases,
                        "completed_cases": full_run.completed_cases,
                        "passed_cases": full_run.passed_cases,
                        "failed_cases": full_run.failed_cases,
                        "pass_rate": round(full_run.pass_rate * 100, 2) if full_run.pass_rate is not None else 0.0,
                        "avg_latency_ms": full_run.avg_latency_ms,
                        "median_latency_ms": summary_metrics.get("p50_latency_ms") or summary_metrics.get("median_latency_ms"),
                        "p95_latency_ms": summary_metrics.get("p95_latency_ms"),
                        "tokens_per_second": tps_overall,
                        "status": full_run.status.upper(),
                        "metrics": {
                            "exact_match": exact_match_score,
                            "accuracy": full_run.pass_rate,
                        },
                    }

                    dur_ms = None
                    if getattr(full_run, "duration_seconds", None) is not None:
                        dur_ms = round(float(full_run.duration_seconds) * 1000, 2)
                    elif getattr(full_run, "created_at", None) and getattr(full_run, "completed_at", None):
                        dur_ms = round((full_run.completed_at - full_run.created_at).total_seconds() * 1000, 2)

                    return {
                        "id": full_run.id,
                        "execution_id": full_run.id,
                        "name": full_run.name,
                        "status": full_run.status.upper(),
                        "dataset_name": full_run.dataset_name or "Evaluation Benchmark",
                        "models": [full_run.model_id],
                        "evaluators": list(summary_metrics.get("metric_averages", {}).keys()) or ["exact_match"],
                        "total_cases": full_run.total_cases,
                        "completed_cases": full_run.completed_cases,
                        "passed_cases": full_run.passed_cases,
                        "failed_cases": full_run.failed_cases,
                        "pass_rate": round(full_run.pass_rate * 100, 2) if full_run.pass_rate is not None else 0.0,
                        "avg_latency_ms": full_run.avg_latency_ms,
                        "median_latency_ms": summary_metrics.get("p50_latency_ms"),
                        "p95_latency_ms": summary_metrics.get("p95_latency_ms"),
                        "tokens_per_second": tps_overall,
                        "total_duration_ms": dur_ms,
                        "created_at": full_run.created_at.isoformat() if hasattr(full_run.created_at, "isoformat") else str(full_run.created_at or ""),
                        "completed_at": full_run.completed_at.isoformat() if full_run.completed_at and hasattr(full_run.completed_at, "isoformat") else (str(full_run.completed_at) if full_run.completed_at else None),
                        "model_summaries": [model_summary],
                        "case_results": c_items,
                        "disagreements": [],
                        "distribution": {
                            "passed": full_run.passed_cases,
                            "failed": full_run.failed_cases,
                            "skipped": max(0, full_run.total_cases - full_run.completed_cases),
                        },
                    }

        # If not found in EvaluationRun, check if execution_id is directly an ExperimentRecord id
        async with get_db_context() as session:
            single_exp = await session.get(ExperimentRecord, execution_id)
            if single_exp:
                experiments = [single_exp]

    if not experiments:
        # Check if execution record exists even with 0 experiments
        if exec_rec:
            return {
                "id": execution_id,
                "execution_id": execution_id,
                "name": "Evaluation Workflow Run",
                "status": exec_rec.status,
                "dataset_name": "Canvas Workflow",
                "models": [],
                "evaluators": [],
                "total_cases": exec_rec.total_steps,
                "completed_cases": exec_rec.completed_steps,
                "passed_cases": 0,
                "failed_cases": 0,
                "pass_rate": 0.0,
                "avg_latency_ms": None,
                "total_duration_ms": None,
                "created_at": exec_rec.started_at.isoformat() if exec_rec.started_at else None,
                "completed_at": exec_rec.completed_at.isoformat() if exec_rec.completed_at else None,
                "error_message": exec_rec.error_message,
                "model_summaries": [],
                "case_results": [],
                "disagreements": [],
                "distribution": {"passed": 0, "failed": 0, "skipped": 0},
            }
        raise HTTPException(status_code=404, detail=f"Evaluation or Execution run '{execution_id}' not found.")

    # 4. Aggregate data across ExperimentRecords
    model_summaries = []
    all_case_results = []
    all_evaluators: set[str] = set()
    model_names: list[str] = []
    workflow_name = experiments[0].name.split(" - ")[0] if " - " in experiments[0].name else experiments[0].name

    for exp in experiments:
        m_id = exp.model_identifier
        model_names.append(m_id)
        ev_ids = json.loads(exp.evaluator_ids_json or "[]")
        for ev in ev_ids:
            all_evaluators.add(ev)

        metrics = json.loads(exp.metrics_json or "{}")
        params = json.loads(exp.parameters_json or "{}")
        cases = params.get("cases", [])

        # Enrich cases with model_id
        for c in cases:
            c_copy = dict(c)
            c_copy["model_id"] = m_id
            c_copy["case_id"] = str(c.get("case_index") or len(all_case_results) + 1)
            all_case_results.append(c_copy)

        pass_rate_val = metrics.get("pass_rate")
        pass_rate_pct = round(pass_rate_val * 100, 2) if pass_rate_val is not None else 0.0

        # Exact match and accuracy metrics extraction
        exact_match_score = metrics.get("exact_match")
        accuracy_score = metrics.get("accuracy") or metrics.get("accuracy_score")
        if accuracy_score is None and pass_rate_val is not None:
            accuracy_score = pass_rate_val
        if exact_match_score is None and "exact_match" in ev_ids:
            exact_match_score = pass_rate_val

        # Measured throughput from token metrics or case timings
        tps_val = metrics.get("tokens_per_second") or metrics.get("avg_tokens_per_second") or metrics.get("avg_throughput_tok_s")
        if tps_val is None:
            # Check individual cases for token measurements
            case_tps = [
                c.get("tokens_per_second")
                for c in cases
                if c.get("tokens_per_second") is not None
            ]
            if case_tps:
                tps_val = round(sum(case_tps) / len(case_tps), 2)

        model_summaries.append({
            "model_id": m_id,
            "name": m_id,
            "total_cases": metrics.get("total_cases", len(cases)),
            "completed_cases": len(cases),
            "passed_cases": metrics.get("passed_cases", sum(1 for c in cases if c.get("passed"))),
            "failed_cases": sum(1 for c in cases if not c.get("passed")),
            "pass_rate": pass_rate_pct,
            "avg_latency_ms": metrics.get("avg_latency_ms"),
            "median_latency_ms": metrics.get("median_latency_ms") or metrics.get("p50_latency_ms"),
            "p95_latency_ms": metrics.get("p95_latency_ms"),
            "tokens_per_second": tps_val,
            "status": exp.status,
            "metrics": {
                **{k: v for k, v in metrics.items() if k not in ("total_cases", "passed_cases", "pass_rate", "avg_latency_ms")},
                "accuracy": accuracy_score,
                "exact_match": exact_match_score,
            },
        })

    # Overall totals
    total_cases_count = sum(s["total_cases"] for s in model_summaries)
    completed_cases_count = sum(s["completed_cases"] for s in model_summaries)
    passed_cases_count = sum(s["passed_cases"] for s in model_summaries)
    failed_cases_count = sum(s["failed_cases"] for s in model_summaries)
    overall_pass_rate = (
        round((passed_cases_count / completed_cases_count) * 100, 2)
        if completed_cases_count > 0
        else 0.0
    )
    latencies = [s["avg_latency_ms"] for s in model_summaries if s["avg_latency_ms"] is not None]
    overall_avg_lat = round(sum(latencies) / len(latencies), 2) if latencies else None

    # Compute execution duration
    duration_ms = None
    if exec_rec and exec_rec.started_at and exec_rec.completed_at:
        duration_ms = round((exec_rec.completed_at - exec_rec.started_at).total_seconds() * 1000, 2)

    # Disagreement detection between multiple models on the same test prompt
    disagreements = []
    if len(model_names) >= 2:
        prompt_map: dict[str, dict[str, dict[str, Any]]] = {}
        for c in all_case_results:
            p_text = c.get("prompt", "").strip()
            prompt_map.setdefault(p_text, {})[c["model_id"]] = c

        for p_text, m_results in prompt_map.items():
            if len(m_results) >= 2:
                passed_states = set(res.get("passed") for res in m_results.values())
                outputs = set(res.get("actual_output", "").strip() for res in m_results.values())
                if len(passed_states) > 1 or len(outputs) > 1:
                    disagreements.append({
                        "prompt": p_text,
                        "results": {
                            m: {
                                "passed": res.get("passed"),
                                "output": res.get("actual_output"),
                                "latency_ms": res.get("latency_ms"),
                            }
                            for m, res in m_results.items()
                        },
                    })

    status_str = exec_rec.status if exec_rec else experiments[0].status

    return {
        "id": execution_id,
        "execution_id": execution_id,
        "name": workflow_name,
        "status": status_str,
        "dataset_name": experiments[0].dataset_id or "Workflow Evaluation Dataset",
        "models": model_names,
        "evaluators": sorted(list(all_evaluators)),
        "total_cases": total_cases_count,
        "completed_cases": completed_cases_count,
        "passed_cases": passed_cases_count,
        "failed_cases": failed_cases_count,
        "pass_rate": overall_pass_rate,
        "avg_latency_ms": overall_avg_lat,
        "total_duration_ms": duration_ms,
        "created_at": (exec_rec.started_at.isoformat() if exec_rec and exec_rec.started_at else experiments[0].created_at.isoformat()) if hasattr(experiments[0].created_at, "isoformat") else str(experiments[0].created_at or ""),
        "completed_at": (exec_rec.completed_at.isoformat() if exec_rec and exec_rec.completed_at else None),
        "model_summaries": model_summaries,
        "case_results": all_case_results,
        "disagreements": disagreements,
        "distribution": {
            "passed": passed_cases_count,
            "failed": failed_cases_count,
            "skipped": max(0, total_cases_count - completed_cases_count),
        },
    }


@router.post("/{execution_id}/cancel")
async def cancel_execution(execution_id: str) -> dict[str, Any]:
    scheduler = get_workflow_scheduler()
    success = scheduler.cancel_execution(execution_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"No active execution found for '{execution_id}' to cancel.")

    broadcaster = get_event_broadcaster()
    await broadcaster.broadcast(
        execution_id=execution_id,
        event_type="cancelled",
        message="Workflow execution cancelled by user request.",
    )

    try:
        from datetime import UTC, datetime
        async with get_db_context() as session:
            rec = await session.get(ExecutionRecord, execution_id)
            if rec:
                rec.status = "CANCELLED"
                rec.completed_at = datetime.now(UTC)
                await session.commit()
    except Exception:
        pass

    return {"success": True, "execution_id": execution_id, "status": "CANCELLED"}

