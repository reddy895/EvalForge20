"""Exponential backoff retry handler for transient provider errors."""

import asyncio
from typing import Any, Callable, TypeVar

T = TypeVar("T")

async def execute_with_retry(
    coro_func: Callable[[], Any],
    max_retries: int = 2,
    base_backoff_seconds: float = 0.05,
) -> T:
    """Execute coroutine with exponential backoff on exceptions."""
    last_err: Exception | None = None
    for attempt in range(max_retries + 1):
        try:
            return await coro_func()
        except Exception as err:
            last_err = err
            if attempt == max_retries:
                break
            await asyncio.sleep(base_backoff_seconds * (2**attempt))
    raise last_err or RuntimeError("Execution failed without exception")
