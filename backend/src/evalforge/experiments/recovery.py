"""Recovery helpers for evaluation runs interrupted by process restarts."""

from datetime import UTC, datetime

from sqlalchemy import select

from src.evalforge.core.logging import get_logger
from src.evalforge.storage.database import get_session_factory
from src.evalforge.storage.models.evaluation import EvaluationRun

logger = get_logger("evalforge.experiments.recovery")

INTERRUPTED_MESSAGE = (
    "Evaluation was interrupted by a server restart before it completed. "
    "Partial case results may be available; re-run the evaluation to obtain a complete result."
)


async def recover_interrupted_runs() -> int:
    """Mark queued/running runs as interrupted on startup.

    Background evaluation tasks live in the application process. If the process
    exits, those tasks are lost; leaving rows in ``running`` would misrepresent
    the run as still active indefinitely.
    """
    session_factory = get_session_factory()
    async with session_factory() as session:
        result = await session.execute(
            select(EvaluationRun).where(EvaluationRun.status.in_(["queued", "running"]))
        )
        stale_runs = list(result.scalars().all())
        if not stale_runs:
            return 0

        now = datetime.now(UTC)
        for run in stale_runs:
            run.status = "interrupted"
            run.error_message = INTERRUPTED_MESSAGE
            run.completed_at = now
        await session.commit()

    logger.warning("Marked %d interrupted evaluation run(s) after startup.", len(stale_runs))
    return len(stale_runs)
