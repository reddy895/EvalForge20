"""AgentEvaluation and AgentTrace specialized repository."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.evalforge.storage.models.agent import AgentEvaluation, AgentTrace
from src.evalforge.storage.repositories.base import BaseRepository


class AgentRepository(BaseRepository[AgentEvaluation]):
    """Specialized repository for agent evaluations and detailed tool invocation traces."""

    def __init__(self, session: AsyncSession):
        super().__init__(session=session, model_cls=AgentEvaluation)

    async def get_with_traces(self, evaluation_id: str) -> AgentEvaluation | None:
        """Fetch agent evaluation run eager-loading all step traces."""
        stmt = (
            select(AgentEvaluation)
            .where(AgentEvaluation.id == evaluation_id)
            .options(selectinload(AgentEvaluation.traces))
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def add_traces(self, evaluation_id: str, traces: list[AgentTrace]) -> list[AgentTrace]:
        """Batch save agent tool execution step traces."""
        for trace in traces:
            trace.evaluation_id = evaluation_id
            self.session.add(trace)
        await self.session.flush()
        return traces

    async def list_traces(self, evaluation_id: str) -> list[AgentTrace]:
        """Retrieve ordered tool trace sequence for an evaluation run."""
        stmt = (
            select(AgentTrace)
            .where(AgentTrace.evaluation_id == evaluation_id)
            .order_by(AgentTrace.step_number)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
