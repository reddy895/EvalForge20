"""Exponential backoff retry handler for transient provider errors."""

import asyncio
from collections.abc import Callable
from typing import Any, TypeVar
import httpx

from src.evalforge.core.errors import ModelNotFoundError, ProviderError

T = TypeVar("T")

TRANSIENT_EXCEPTIONS = (
    httpx.ConnectError,
    httpx.ReadTimeout,
    httpx.ConnectTimeout,
    httpx.RemoteProtocolError,
    TimeoutError,
    ConnectionResetError,
)


async def execute_with_retry(
    coro_func: Callable[[], Any],
    max_retries: int = 2,
    base_backoff_seconds: float = 0.05,
    retryable_exceptions: tuple = TRANSIENT_EXCEPTIONS,
) -> T:
    """Execute coroutine with exponential backoff on transient network exceptions."""
    last_err: Exception | None = None
    for attempt in range(max_retries + 1):
        try:
            return await coro_func()
        except ModelNotFoundError:
            # Fatal error: do not retry if model does not exist
            raise
        except Exception as err:
            last_err = err
            # If not a transient error, re-raise immediately
            if not isinstance(err, retryable_exceptions):
                raise
            if attempt == max_retries:
                break
            await asyncio.sleep(base_backoff_seconds * (2**attempt))
    raise last_err or RuntimeError("Execution failed without exception")
