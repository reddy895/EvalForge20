"""Unit tests for Ollama pull monitor and offline diagnostics."""

import pytest

from src.evalforge.providers.ollama.diagnostics import run_ollama_diagnostics
from src.evalforge.providers.ollama.pull_monitor import parse_pull_event


def test_parse_pull_event() -> None:
    event = parse_pull_event({"status": "downloading", "digest": "sha256:123", "total": 1000, "completed": 500})
    assert event.status == "downloading"
    assert event.percent == 50.0
    assert event.digest == "sha256:123"

@pytest.mark.asyncio
async def test_ollama_diagnostics_unreachable() -> None:
    report = await run_ollama_diagnostics("http://localhost:59999")
    assert report.reachable is False
    assert "ollama serve" in (report.remediation_hint or "").lower()
