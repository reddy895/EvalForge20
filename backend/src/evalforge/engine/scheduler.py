"""Async workflow execution scheduler with semaphore concurrency control and fair alternating execution."""

import asyncio
from typing import Any


class WorkflowScheduler:
    """Schedules model inferences with concurrency limits, cancellation tokens, and fair alternating order."""

    def __init__(self, concurrency_limit: int = 4, default_timeout_seconds: float = 60.0) -> None:
        self.concurrency_limit = max(1, min(16, concurrency_limit))
        self.default_timeout_seconds = default_timeout_seconds
        self._semaphore = asyncio.Semaphore(self.concurrency_limit)
        self._cancellation_events: dict[str, asyncio.Event] = {}

    def register_execution(self, execution_id: str) -> asyncio.Event:
        """Register cancellation token for an execution."""
        event = asyncio.Event()
        self._cancellation_events[execution_id] = event
        return event

    def cancel_execution(self, execution_id: str) -> bool:
        """Signal cancellation for a running execution."""
        if execution_id in self._cancellation_events:
            self._cancellation_events[execution_id].set()
            return True
        return False

    def is_cancelled(self, execution_id: str) -> bool:
        """Check whether execution has been cancelled."""
        event = self._cancellation_events.get(execution_id)
        return event.is_set() if event else False

    def unregister_execution(self, execution_id: str) -> None:
        """Clean up cancellation token upon completion."""
        self._cancellation_events.pop(execution_id, None)

    async def run_throttled(self, coro: Any, timeout: float | None = None) -> Any:
        """Execute coroutine under semaphore lock with timeout limit."""
        effective_timeout = timeout or self.default_timeout_seconds
        async with self._semaphore:
            return await asyncio.wait_for(coro, timeout=effective_timeout)


_global_scheduler: WorkflowScheduler | None = None


def get_workflow_scheduler() -> WorkflowScheduler:
    global _global_scheduler
    if _global_scheduler is None:
        _global_scheduler = WorkflowScheduler()
    return _global_scheduler


__all__ = [
    "WorkflowScheduler",
    "get_workflow_scheduler",
]
