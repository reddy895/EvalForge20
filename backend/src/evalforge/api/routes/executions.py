"""Modular API routes for workflow execution triggers, SSE streaming, and cancellation."""

import asyncio
import json
import uuid
from typing import Any
from fastapi import APIRouter, BackgroundTasks, HTTPException
from fastapi.responses import StreamingResponse

from src.evalforge.database.models import ExecutionRecord, WorkflowRecord
from src.evalforge.database.session import get_db_context
from src.evalforge.engine.events import get_event_broadcaster
from src.evalforge.engine.executor import get_workflow_executor
from src.evalforge.engine.scheduler import get_workflow_scheduler
from src.evalforge.schemas.main import ExecutionTriggerRequest, WorkflowGraph

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

    return {"success": True, "execution_id": execution_id, "status": "CANCELLED"}
