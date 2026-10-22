"""Ollama model pull event stream parser and progress tracker."""

from dataclasses import dataclass
from typing import Any


@dataclass
class PullProgressEvent:
    status: str
    digest: str | None
    total_bytes: int
    completed_bytes: int
    percent: float

def parse_pull_event(payload: dict[str, Any]) -> PullProgressEvent:
    """Parse JSON line from Ollama POST /api/pull stream."""
    status = payload.get("status", "pending")
    digest = payload.get("digest")
    total = int(payload.get("total", 0))
    completed = int(payload.get("completed", 0))
    percent = round((completed / total) * 100.0, 1) if total > 0 else 0.0

    return PullProgressEvent(
        status=status,
        digest=digest,
        total_bytes=total,
        completed_bytes=completed,
        percent=percent,
    )
