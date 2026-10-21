"""API endpoints for Agent evaluation and tool execution trace retrieval."""

import json
from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.evalforge.schemas.agent import (
    AgentEvaluationCreateRequest,
    AgentEvaluationDetailResponse,
    AgentEvaluationResponse,
    AgentStepTrace,
)
from src.evalforge.services.agent_service import AgentService
from src.evalforge.storage.database import get_db

agents_router = APIRouter(prefix="/agent-evaluations", tags=["Agent Evaluations"])


def _map_agent_response(run: object) -> AgentEvaluationResponse:
    """Helper mapping AgentEvaluation model to AgentEvaluationResponse schema."""
    return AgentEvaluationResponse(
        id=run.id,  # type: ignore[attr-defined]
        name=run.name,  # type: ignore[attr-defined]
        model_id=run.model_id,  # type: ignore[attr-defined]
        provider=run.provider,  # type: ignore[attr-defined]
        task=run.task,  # type: ignore[attr-defined]
        status=run.status,  # type: ignore[attr-defined]
        total_steps=run.total_steps,  # type: ignore[attr-defined]
        max_steps=run.max_steps,  # type: ignore[attr-defined]
        task_completed=run.task_completed,  # type: ignore[attr-defined]
        tool_accuracy=run.tool_accuracy,  # type: ignore[attr-defined]
        schema_validity=run.schema_validity,  # type: ignore[attr-defined]
        policy_violations=run.policy_violations,  # type: ignore[attr-defined]
        final_output=run.final_output,  # type: ignore[attr-defined]
        error_message=run.error_message,  # type: ignore[attr-defined]
        created_at=run.created_at.isoformat(),  # type: ignore[attr-defined]
    )


@agents_router.post(
    "",
    response_model=AgentEvaluationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Execute a controlled agent evaluation run",
)
async def create_agent_evaluation(
    payload: AgentEvaluationCreateRequest,
    db: AsyncSession = Depends(get_db),
) -> AgentEvaluationResponse:
    """Run an agent interaction loop with sandboxed tools and step-level auditing."""
    service = AgentService(db)
    evaluation = await service.run_evaluation(payload)
    return _map_agent_response(evaluation)


@agents_router.get(
    "/{evaluation_id}",
    response_model=AgentEvaluationResponse,
    summary="Get agent evaluation status and metrics",
)
async def get_agent_evaluation(
    evaluation_id: str,
    db: AsyncSession = Depends(get_db),
) -> AgentEvaluationResponse:
    """Fetch status, tool accuracy, and outcome of an agent evaluation."""
    service = AgentService(db)
    evaluation = await service.get_evaluation(evaluation_id)
    return _map_agent_response(evaluation)


@agents_router.get(
    "/{evaluation_id}/traces",
    response_model=List[AgentStepTrace],
    summary="Get ordered execution traces for an agent evaluation",
)
async def get_agent_traces(
    evaluation_id: str,
    db: AsyncSession = Depends(get_db),
) -> List[AgentStepTrace]:
    """Retrieve chronologically ordered tool calls, arguments, outputs, and reasoning steps."""
    service = AgentService(db)
    traces = await service.get_traces(evaluation_id)

    results = []
    for t in traces:
        results.append(
            AgentStepTrace(
                step_number=t.step_number,
                tool_name=t.tool_name,
                tool_args=t.tool_args,
                tool_result=t.tool_result,
                thought=t.thought,
                duration_ms=t.duration_ms,
                is_valid_call=t.is_valid_call,
            )
        )
    return results
