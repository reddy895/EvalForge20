"""Modular API routes for visual workflow canvas CRUD and topological graph validation."""

import json
from typing import Any
from fastapi import APIRouter, HTTPException
from sqlalchemy import delete, desc, select

from src.evalforge.database.models import WorkflowRecord
from src.evalforge.database.session import get_db_context
from src.evalforge.engine.validator import WorkflowValidator
from src.evalforge.schemas.main import (
    WorkflowCreateRequest,
    WorkflowGraph,
    WorkflowResponse,
    WorkflowUpdateRequest,
    WorkflowValidationResult,
)

router = APIRouter(prefix="/workflows", tags=["workflows"])


@router.get("")
async def list_workflows(limit: int = 50, offset: int = 0) -> dict[str, Any]:
    async with get_db_context() as session:
        stmt = (
            select(WorkflowRecord)
            .where(WorkflowRecord.is_active == True)
            .order_by(desc(WorkflowRecord.updated_at))
            .offset(offset)
            .limit(limit)
        )
        res = await session.execute(stmt)
        workflows = res.scalars().all()

        return {
            "total": len(workflows),
            "workflows": [
                {
                    "id": w.id,
                    "name": w.name,
                    "description": w.description,
                    "graph": json.loads(w.graph_json),
                    "created_at": w.created_at.isoformat(),
                    "updated_at": w.updated_at.isoformat(),
                }
                for w in workflows
            ],
        }


@router.post("")
async def create_workflow(payload: WorkflowCreateRequest) -> dict[str, Any]:
    async with get_db_context() as session:
        record = WorkflowRecord(
            name=payload.name,
            description=payload.description,
            graph_json=payload.graph.model_dump_json(),
        )
        session.add(record)
        await session.commit()
        await session.refresh(record)

        return {
            "id": record.id,
            "name": record.name,
            "description": record.description,
            "graph": json.loads(record.graph_json),
            "created_at": record.created_at.isoformat(),
            "updated_at": record.updated_at.isoformat(),
        }


@router.get("/{workflow_id}")
async def get_workflow(workflow_id: str) -> dict[str, Any]:
    async with get_db_context() as session:
        stmt = select(WorkflowRecord).where(WorkflowRecord.id == workflow_id)
        res = await session.execute(stmt)
        record = res.scalar_one_or_none()
        if not record:
            raise HTTPException(status_code=404, detail=f"Workflow '{workflow_id}' not found.")

        return {
            "id": record.id,
            "name": record.name,
            "description": record.description,
            "graph": json.loads(record.graph_json),
            "created_at": record.created_at.isoformat(),
            "updated_at": record.updated_at.isoformat(),
        }


@router.put("/{workflow_id}")
async def update_workflow(workflow_id: str, payload: WorkflowUpdateRequest) -> dict[str, Any]:
    async with get_db_context() as session:
        stmt = select(WorkflowRecord).where(WorkflowRecord.id == workflow_id)
        res = await session.execute(stmt)
        record = res.scalar_one_or_none()
        if not record:
            raise HTTPException(status_code=404, detail=f"Workflow '{workflow_id}' not found.")

        if payload.name is not None:
            record.name = payload.name
        if payload.description is not None:
            record.description = payload.description
        if payload.graph is not None:
            record.graph_json = payload.graph.model_dump_json()
        if payload.is_active is not None:
            record.is_active = payload.is_active

        await session.commit()
        await session.refresh(record)

        return {
            "id": record.id,
            "name": record.name,
            "description": record.description,
            "graph": json.loads(record.graph_json),
            "created_at": record.created_at.isoformat(),
            "updated_at": record.updated_at.isoformat(),
        }


@router.delete("/{workflow_id}")
async def delete_workflow(workflow_id: str) -> dict[str, Any]:
    async with get_db_context() as session:
        stmt = delete(WorkflowRecord).where(WorkflowRecord.id == workflow_id)
        res = await session.execute(stmt)
        await session.commit()
        if res.rowcount == 0:
            raise HTTPException(status_code=404, detail=f"Workflow '{workflow_id}' not found.")
        return {"success": True, "deleted_id": workflow_id}


@router.post("/validate")
async def validate_workflow(payload: WorkflowGraph) -> dict[str, Any]:
    res = WorkflowValidator.validate_graph(payload)
    return res.model_dump()
