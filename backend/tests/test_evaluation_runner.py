"""Unit tests for EvaluationRunner."""

import pytest

from src.evalforge.evaluation.runner import EvaluationRunner


@pytest.mark.asyncio
async def test_evaluation_runner_batch() -> None:
    runner = EvaluationRunner(max_concurrency=2)
    cases = [{"id": f"case_{i}", "prompt": f"Test {i}"} for i in range(5)]

    async def _mock_exec(c: dict) -> str:
        return f"Echo {c['prompt']}"

    prog = await runner.run_batch("job_1", cases, _mock_exec)
    assert prog.total == 5
    assert prog.completed == 5
    assert prog.failed == 0
    assert prog.status == "completed"

@pytest.mark.asyncio
async def test_evaluation_runner_cancellation() -> None:
    runner = EvaluationRunner()
    runner.cancel("job_cancel")
    assert runner.is_cancelled("job_cancel") is True
