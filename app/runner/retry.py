"""Retry policy and classification of safe-to-retry errors."""

import asyncio
from collections.abc import Awaitable, Callable
from typing import TypeVar

from app.domain.contracts import ProviderResponse
from app.domain.errors import NormalizedErrorCategory

T = TypeVar("T")

SAFE_TO_RETRY_CATEGORIES = {
    NormalizedErrorCategory.TIMEOUT.value,
    NormalizedErrorCategory.RATE_LIMIT.value,
    NormalizedErrorCategory.PROVIDER_UNAVAILABLE.value,
}


def is_safe_to_retry(error_category: str | None) -> bool:
    """Return True if an error category is considered safe for automatic retry."""
    if not error_category:
        return False
    return error_category in SAFE_TO_RETRY_CATEGORIES


async def execute_with_retry(
    action: Callable[[], Awaitable[ProviderResponse]],
    max_retries: int = 2,
    initial_delay_seconds: float = 0.5,
) -> ProviderResponse:
    """Execute provider call with bounded exponential retries for safe-to-retry errors."""
    attempts = 0
    delay = initial_delay_seconds

    while True:
        attempts += 1
        resp = await action()

        if resp.is_success or attempts > max_retries:
            return resp

        if not is_safe_to_retry(resp.error_category):
            # Non-retryable error (e.g. auth failure or schema error)
            return resp

        # Safe to retry, wait backoff delay
        await asyncio.sleep(delay)
        delay = min(delay * 2.0, 5.0)
