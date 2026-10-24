"""EvaluationRun and CaseResult specialized repository."""

from datetime import UTC, datetime

from sqlalchemy import desc, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.evalforge.storage.models.evaluation import CaseResult, EvaluationRun
from src.evalforge.storage.repositories.base import BaseRepository


class EvaluationRepository(BaseRepository[EvaluationRun]):
    """Specialized repository for evaluation runs and granular case results."""

    def __init__(self, session: AsyncSession):
        super().__init__(session=session, model_cls=EvaluationRun)

    async def get_with_results(self, evaluation_id: str) -> EvaluationRun | None:
        """Fetch evaluation run eager-loading all case-level results."""
        stmt = (
            select(EvaluationRun)
            .where(EvaluationRun.id == evaluation_id)
            .options(selectinload(EvaluationRun.results))
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_evaluations(
        self,
        status: str | None = None,
        model_id: str | None = None,
        dataset_id: str | None = None,
        query: str | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[list[EvaluationRun], int]:
        """Filter evaluations with pagination, search, descending timestamp order, and total matching count."""
        count_stmt = select(func.count(EvaluationRun.id))
        stmt = select(EvaluationRun)
        if status:
            count_stmt = count_stmt.where(EvaluationRun.status == status)
            stmt = stmt.where(EvaluationRun.status == status)
        if model_id:
            count_stmt = count_stmt.where(EvaluationRun.model_id == model_id)
            stmt = stmt.where(EvaluationRun.model_id == model_id)
        if dataset_id:
            count_stmt = count_stmt.where(EvaluationRun.dataset_id == dataset_id)
            stmt = stmt.where(EvaluationRun.dataset_id == dataset_id)
        if query:
            search_clause = (
                EvaluationRun.name.ilike(f"%{query}%")
                | EvaluationRun.model_id.ilike(f"%{query}%")
                | EvaluationRun.dataset_name.ilike(f"%{query}%")
            )
            count_stmt = count_stmt.where(search_clause)
            stmt = stmt.where(search_clause)

        total_res = await self.session.execute(count_stmt)
        total = total_res.scalar() or 0

        stmt = stmt.order_by(desc(EvaluationRun.created_at)).offset(offset).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all()), total

    async def list_by_filter(
        self,
        status: str | None = None,
        model_id: str | None = None,
        dataset_id: str | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> list[EvaluationRun]:
        """Filter evaluations with pagination and descending timestamp order."""
        runs, _ = await self.list_evaluations(
            status=status,
            model_id=model_id,
            dataset_id=dataset_id,
            offset=offset,
            limit=limit,
        )
        return runs

    async def update_status(
        self,
        evaluation_id: str,
        status: str,
        error_message: str | None = None,
    ) -> None:
        """Atomic status update for evaluation lifecycle progression."""
        values = {"status": status}
        if error_message is not None:
            values["error_message"] = error_message
        if status in ("completed", "completed_with_errors", "failed", "cancelled"):
            values["completed_at"] = datetime.now(UTC)

        stmt = update(EvaluationRun).where(EvaluationRun.id == evaluation_id).values(**values)
        await self.session.execute(stmt)
        await self.session.flush()

    async def add_case_results(
        self, evaluation_id: str, results: list[CaseResult]
    ) -> list[CaseResult]:
        """Batch save case evaluation outcomes."""
        for res in results:
            res.evaluation_id = evaluation_id
            self.session.add(res)
        await self.session.flush()
        return results

    async def get_case_results(
        self, evaluation_id: str, offset: int = 0, limit: int = 100
    ) -> list[CaseResult]:
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
