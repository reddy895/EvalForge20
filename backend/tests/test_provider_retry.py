"""Unit tests for provider retry handler."""

import pytest
from src.evalforge.providers.retry import execute_with_retry

@pytest.mark.asyncio
async def test_execute_with_retry_success() -> None:
    calls = 0
    async def _op() -> str:
        nonlocal calls
        calls += 1
        return "success"
    res = await execute_with_retry(_op, max_retries=2)
    assert res == "success"
    assert calls == 1

@pytest.mark.asyncio
async def test_execute_with_retry_eventual_success() -> None:
    calls = 0
    async def _flaky() -> str:
        nonlocal calls
        calls += 1
        if calls < 2:
            raise ConnectionResetError("Transient network glitch")
        return "recovered"
    res = await execute_with_retry(_flaky, max_retries=2)
    assert res == "recovered"
    assert calls == 2
