"""Server-Sent Events (SSE) broadcaster for real-time workflow execution progress streaming."""

import asyncio
from collections import defaultdict
from collections.abc import AsyncGenerator
from datetime import UTC, datetime
from typing import Any

from src.evalforge.schemas.main import ExecutionEvent


class ExecutionEventBroadcaster:
    """Manages active SSE subscriber queues and broadcasts structured execution events."""

    def __init__(self) -> None:
        self._listeners: dict[str, list[asyncio.Queue[ExecutionEvent | None]]] = defaultdict(list)
        self._history: dict[str, list[ExecutionEvent]] = defaultdict(list)

    def subscribe(self, execution_id: str) -> asyncio.Queue[ExecutionEvent | None]:
        """Subscribe to live events for an execution."""
        queue: asyncio.Queue[ExecutionEvent | None] = asyncio.Queue()
        # Replay past events in case client connected slightly after start
        for past_ev in self._history.get(execution_id, []):
            queue.put_nowait(past_ev)
        self._listeners[execution_id].append(queue)
        return queue

    def unsubscribe(self, execution_id: str, queue: asyncio.Queue[ExecutionEvent | None]) -> None:
        """Remove a subscriber queue."""
        if execution_id in self._listeners:
            try:
                self._listeners[execution_id].remove(queue)
            except ValueError:
                pass
            if not self._listeners[execution_id]:
                self._listeners.pop(execution_id, None)

    async def broadcast(
        self,
        execution_id: str,
        event_type: str,
        message: str,
        progress_percentage: float = 0.0,
        completed_steps: int = 0,
        total_steps: int = 0,
        data: dict[str, Any] | None = None,
    ) -> ExecutionEvent:
        """Publish an execution event to all active subscribers."""
        ev = ExecutionEvent(
            execution_id=execution_id,
            event_type=event_type,  # type: ignore[arg-type]
            timestamp=datetime.now(UTC).isoformat(),
            message=message,
            progress_percentage=round(progress_percentage, 1),
            completed_steps=completed_steps,
            total_steps=total_steps,
            data=data or {},
        )
        self._history[execution_id].append(ev)

        listeners = list(self._listeners.get(execution_id, []))
        for q in listeners:
            q.put_nowait(ev)

        # If terminal event, close subscriber queues with None sentinel
        if event_type in ("completed", "failed", "cancelled"):
            for q in listeners:
                q.put_nowait(None)

        return ev

    async def stream_events(self, execution_id: str) -> AsyncGenerator[str, None]:
        """Yield formatted SSE chunks: data: {...}\n\n"""
        queue = self.subscribe(execution_id)
        try:
            while True:
                ev = await queue.get()
                if ev is None:
                    break
                yield f"data: {ev.model_dump_json()}\n\n"
        finally:
            self.unsubscribe(execution_id, queue)


_global_broadcaster: ExecutionEventBroadcaster | None = None


def get_event_broadcaster() -> ExecutionEventBroadcaster:
    global _global_broadcaster
    if _global_broadcaster is None:
        _global_broadcaster = ExecutionEventBroadcaster()
    return _global_broadcaster


__all__ = [
    "ExecutionEventBroadcaster",
    "get_event_broadcaster",
]
