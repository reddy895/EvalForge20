"""EvaluationRun and CaseResult specialized repository."""

from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy import desc, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.evalforge.storage.models.evaluation import CaseResult, EvaluationRun
from src.evalforge.storage.repositories.base import BaseRepository


class EvaluationRepository(BaseRepository[EvaluationRun]):
    """Specialized repository for evaluation runs and granular case results."""

    def __init__(self, session: AsyncSession):
        super().__init__(session=session, model_cls=EvaluationRun)

    async def get_with_results(self, evaluation_id: str) -> Optional[EvaluationRun]:
        """Fetch evaluation run eager-loading all case-level results."""
        stmt = (
            select(EvaluationRun)
            .where(EvaluationRun.id == evaluation_id)
            .options(selectinload(EvaluationRun.results))
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_by_filter(
        self,
        status: Optional[str] = None,
        model_id: Optional[str] = None,
        dataset_id: Optional[str] = None,
        offset: int = 0,
        limit: int = 50,
    ) -> List[EvaluationRun]:
        """Filter evaluations with pagination and descending timestamp order."""
        stmt = select(EvaluationRun)
        if status:
            stmt = stmt.where(EvaluationRun.status == status)
        if model_id:
            stmt = stmt.where(EvaluationRun.model_id == model_id)
        if dataset_id:
            stmt = stmt.where(EvaluationRun.dataset_id == dataset_id)

        stmt = stmt.order_by(desc(EvaluationRun.created_at)).offset(offset).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def update_status(
        self,
        evaluation_id: str,
        status: str,
        error_message: Optional[str] = None,
    ) -> None:
        """Atomic status update for evaluation lifecycle progression."""
        values = {"status": status}
        if error_message is not None:
            values["error_message"] = error_message
        if status in ("completed", "failed", "cancelled"):
            values["completed_at"] = datetime.now(timezone.utc)

        stmt = (
            update(EvaluationRun)
            .where(EvaluationRun.id == evaluation_id)
            .values(**values)
        )
        await self.session.execute(stmt)
        await self.session.flush()

    async def add_case_results(
        self, evaluation_id: str, results: List[CaseResult]
    ) -> List[CaseResult]:
        """Batch save case evaluation outcomes."""
        for res in results:
            res.evaluation_id = evaluation_id
            self.session.add(res)
        await self.session.flush()
        return results

    async def get_case_results(
        self, evaluation_id: str, offset: int = 0, limit: int = 100
    ) -> List[CaseResult]:
        """Fetch paginated case-level results for a specific evaluation."""
        stmt = (
            select(CaseResult)
            .where(CaseResult.evaluation_id == evaluation_id)
            .order_by(CaseResult.created_at)
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
