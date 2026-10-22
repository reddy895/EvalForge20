"""Evaluation job execution runner with cancellation and concurrency limits."""

import asyncio
from dataclasses import dataclass, field
from typing import Any, Callable

@dataclass
class JobProgress:
    total: int
    completed: int = 0
    failed: int = 0
    status: str = "queued"
    results: list[dict[str, Any]] = field(default_factory=list)

class EvaluationRunner:
    """Dispatches test cases with bounded concurrency and cancellation detection."""

    def __init__(self, max_concurrency: int = 4):
        self.max_concurrency = max(1, min(max_concurrency, 16))
        self._cancel_signals: set[str] = set()

    def cancel(self, job_id: str) -> None:
        self._cancel_signals.add(job_id)

    def is_cancelled(self, job_id: str) -> bool:
        return job_id in self._cancel_signals

    async def run_batch(
        self,
        job_id: str,
        cases: list[dict[str, Any]],
        executor: Callable[[dict[str, Any]], Any],
        on_progress: Callable[[JobProgress], None] | None = None,
    ) -> JobProgress:
        progress = JobProgress(total=len(cases), status="running")
        sem = asyncio.Semaphore(self.max_concurrency)

        async def _exec_case(case: dict[str, Any]) -> None:
            if self.is_cancelled(job_id):
                progress.status = "cancelled"
                return

            async with sem:
                try:
                    res = await executor(case)
                    progress.completed += 1
                    progress.results.append({"case_id": case.get("id"), "passed": True, "result": res})
                except Exception as err:
                    progress.failed += 1
                    progress.results.append({"case_id": case.get("id"), "passed": False, "error": str(err)})

            if on_progress:
                on_progress(progress)

        tasks = [_exec_case(c) for c in cases]
        await asyncio.gather(*tasks, return_exceptions=True)

        if not self.is_cancelled(job_id):
            progress.status = "completed" if progress.failed == 0 else "completed_with_errors"

        return progress
