"""Experiment persistence repository handling SQLite storage, retrieval, and serialization."""

import csv
import io
import json
from typing import Any

from sqlalchemy import delete, desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.evalforge.database.models import CaseResultRecord, EvaluationRunRecord, ExperimentRecord
from src.evalforge.database.session import get_db_context


class ExperimentRepository:
    """Async repository managing persistent experiment records."""

    @classmethod
    async def create(
        cls,
        name: str,
        model_identifier: str,
        workflow_id: str | None = None,
        execution_id: str | None = None,
        dataset_id: str | None = None,
        evaluator_ids: list[str] | None = None,
        metrics: dict[str, Any] | None = None,
        parameters: dict[str, Any] | None = None,
        hardware: dict[str, Any] | None = None,
        status: str = "COMPLETED",
        session: AsyncSession | None = None,
    ) -> ExperimentRecord:
        record = ExperimentRecord(
            name=name,
            workflow_id=workflow_id,
            execution_id=execution_id,
            model_identifier=model_identifier,
            dataset_id=dataset_id,
            evaluator_ids_json=json.dumps(evaluator_ids or []),
            metrics_json=json.dumps(metrics or {}),
            parameters_json=json.dumps(parameters or {}),
            hardware_json=json.dumps(hardware or {}),
            status=status,
        )

        if session:
            session.add(record)
            await session.flush()
            return record

        async with get_db_context() as sess:
            sess.add(record)
            await sess.commit()
            await sess.refresh(record)
            return record

    @classmethod
    async def get_by_id(cls, experiment_id: str) -> ExperimentRecord | None:
        async with get_db_context() as session:
            stmt = select(ExperimentRecord).where(ExperimentRecord.id == experiment_id)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

    @classmethod
    async def list_all(
        cls,
        limit: int = 50,
        offset: int = 0,
        model_identifier: str | None = None,
    ) -> list[ExperimentRecord]:
        async with get_db_context() as session:
            stmt = select(ExperimentRecord).order_by(desc(ExperimentRecord.created_at))
            if model_identifier:
                stmt = stmt.where(ExperimentRecord.model_identifier == model_identifier)
            stmt = stmt.offset(offset).limit(limit)
            result = await session.execute(stmt)
            return list(result.scalars().all())

    @classmethod
    async def delete(cls, experiment_id: str) -> bool:
        async with get_db_context() as session:
            stmt = delete(ExperimentRecord).where(ExperimentRecord.id == experiment_id)
            res = await session.execute(stmt)
            await session.commit()
            return res.rowcount > 0

    @classmethod
    async def export_json(cls, experiment_id: str) -> dict[str, Any] | None:
        exp = await cls.get_by_id(experiment_id)
        if not exp:
            return None
        return {
            "id": exp.id,
            "name": exp.name,
            "model_identifier": exp.model_identifier,
            "workflow_id": exp.workflow_id,
            "dataset_id": exp.dataset_id,
            "evaluator_ids": json.loads(exp.evaluator_ids_json),
            "metrics": json.loads(exp.metrics_json),
            "parameters": json.loads(exp.parameters_json),
            "hardware": json.loads(exp.hardware_json),
            "status": exp.status,
            "created_at": exp.created_at.isoformat(),
        }

    @classmethod
    async def export_csv(cls, experiment_id: str) -> str | None:
        data = await cls.export_json(experiment_id)
        if not data:
            return None

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["Field", "Value"])
        for k, v in data.items():
            val = json.dumps(v) if isinstance(v, (dict, list)) else str(v)
            writer.writerow([k, val])
        return output.getvalue()


__all__ = ["ExperimentRepository"]
