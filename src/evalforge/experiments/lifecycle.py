"""Lifecycle coordinator managing run cancellation signals and state."""

import asyncio
from typing import Dict, Optional

from src.evalforge.core.logging import get_logger

logger = get_logger("evalforge.experiments.lifecycle")


class LifecycleCoordinator:
    """Coordinates cancellation events and tracking for active running evaluations."""

    def __init__(self) -> None:
        self._cancellation_events: Dict[str, asyncio.Event] = {}

    def register_run(self, evaluation_id: str) -> asyncio.Event:
        """Register a new run and return its cancellation event."""
        event = asyncio.Event()
        self._cancellation_events[evaluation_id] = event
        return event

    def cancel_run(self, evaluation_id: str) -> bool:
        """Signal cooperative cancellation to an active evaluation."""
        if evaluation_id in self._cancellation_events:
            self._cancellation_events[evaluation_id].set()
            logger.info("Cancellation signal dispatched for evaluation '%s'", evaluation_id)
            return True
        return False

    def is_cancelled(self, evaluation_id: str) -> bool:
        """Check whether cancellation was requested for this evaluation."""
        event = self._cancellation_events.get(evaluation_id)
        return event.is_set() if event else False

    def unregister_run(self, evaluation_id: str) -> None:
        """Clean up cancellation tracking after run finishes or terminates."""
        self._cancellation_events.pop(evaluation_id, None)


_lifecycle_coordinator: Optional[LifecycleCoordinator] = None


def get_lifecycle_coordinator() -> LifecycleCoordinator:
    """Return shared LifecycleCoordinator instance."""
    global _lifecycle_coordinator
    if _lifecycle_coordinator is None:
        _lifecycle_coordinator = LifecycleCoordinator()
    return _lifecycle_coordinator
