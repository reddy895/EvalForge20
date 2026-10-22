"""Bounded concurrency worker pool with cancellation awareness."""

import asyncio
from collections.abc import Awaitable, Callable
from typing import TypeVar

from src.evalforge.core.logging import get_logger

logger = get_logger("evalforge.experiments.concurrency")

T = TypeVar("T")
R = TypeVar("R")


class BoundedConcurrencyPool:
    """Dispatches asynchronous tasks with bounded concurrency and cooperative cancellation checks."""

    def __init__(self, max_concurrency: int = 4):
        self.max_concurrency = max(1, max_concurrency)
        self.semaphore = asyncio.Semaphore(self.max_concurrency)

    async def map(
        self,
        worker_fn: Callable[[T], Awaitable[R]],
        items: list[T],
        cancellation_event: asyncio.Event | None = None,
    ) -> list[R]:
        """Execute worker_fn on each item concurrently up to the semaphore limit."""
        results: list[R | None] = [None] * len(items)

        async def _run_one(index: int, item: T) -> None:
            if cancellation_event and cancellation_event.is_set():
                return

            async with self.semaphore:
                if cancellation_event and cancellation_event.is_set():
                    return
                try:
                    res = await worker_fn(item)
                    results[index] = res
                except Exception as exc:
                    logger.exception("Error processing worker task index %d: %s", index, exc)
                    raise

        tasks = [_run_one(i, item) for i, item in enumerate(items)]
        # return_exceptions=True so that individual failed cases do not abort other running tasks
        await asyncio.gather(*tasks, return_exceptions=True)

        return [r for r in results if r is not None]
