"""Unit tests for Ollama 8-state connectivity diagnostics, pull monitor, and setup advisor."""

from unittest.mock import patch

import httpx
import pytest

from src.evalforge.providers.ollama.diagnostics import run_ollama_diagnostics
from src.evalforge.providers.ollama.pull_monitor import parse_pull_event


def test_parse_pull_event() -> None:
    event = parse_pull_event({"status": "downloading", "digest": "sha256:123", "total": 1000, "completed": 500})
    assert event.status == "downloading"
    assert event.percent == 50.0
    assert event.digest == "sha256:123"


@pytest.mark.asyncio
async def test_ollama_diagnostics_unreachable_offline() -> None:
    report = await run_ollama_diagnostics("http://localhost:59999")
    assert report.reachable is False
    assert report.connectivity_state in ("installed_not_running", "connection_refused")
    assert "ollama serve" in (report.remediation_hint or "").lower() or "https://ollama.com" in (report.remediation_hint or "")


@pytest.mark.asyncio
async def test_ollama_diagnostics_invalid_config_url() -> None:
    # State 8: Invalid configuration / unsupported endpoint
    report = await run_ollama_diagnostics("not_a_valid_url")
    assert report.reachable is False
    assert report.connectivity_state == "invalid_config"
    assert "Invalid URL" in (report.error_message or "")


@pytest.mark.asyncio
async def test_ollama_diagnostics_timeout() -> None:
    # State 4: Timeout
    with patch("httpx.AsyncClient.get", side_effect=httpx.ConnectTimeout("Connection timed out")):
        report = await run_ollama_diagnostics("http://10.255.255.1:11434", timeout=0.1)
        assert report.reachable is False
        assert report.connectivity_state == "timeout"
        assert "timed out" in (report.error_message or "").lower()


@pytest.mark.asyncio
async def test_ollama_diagnostics_installed_not_running() -> None:
    # State 2: Installed locally but not running
    with patch("shutil.which", return_value="/usr/local/bin/ollama"):
        with patch("httpx.AsyncClient.get", side_effect=httpx.ConnectError("Connection refused")):
            report = await run_ollama_diagnostics("http://127.0.0.1:11434")
            assert report.reachable is False
            assert report.connectivity_state == "installed_not_running"
            assert "ollama serve" in (report.remediation_hint or "")


@pytest.mark.asyncio
async def test_ollama_diagnostics_connection_refused_no_binary() -> None:
    # State 3: Connection refused, no local binary
    with patch("shutil.which", return_value=None):
        with patch("httpx.AsyncClient.get", side_effect=httpx.ConnectError("Connection refused")):
            report = await run_ollama_diagnostics("http://192.168.1.100:11434")
            assert report.reachable is False
            assert report.connectivity_state == "connection_refused"


@pytest.mark.asyncio
async def test_ollama_diagnostics_reachable_no_models() -> None:
    # State 5: Reachable but 0 models installed
    mock_resp = httpx.Response(200, json={"models": []}, request=httpx.Request("GET", "http://test"))
    with patch("httpx.AsyncClient.get", return_value=mock_resp):
        report = await run_ollama_diagnostics("http://localhost:11434")
        assert report.reachable is True
        assert report.connectivity_state == "reachable_no_models"
        assert report.installed_models_count == 0
        assert "ollama pull" in (report.remediation_hint or "")


@pytest.mark.asyncio
async def test_ollama_diagnostics_model_ready_and_missing() -> None:
    # State 7: Ready and State 6: Requested model missing
    mock_resp = httpx.Response(200, json={"models": [{"name": "qwen2.5:1.5b"}, {"name": "llama3.2:3b"}]}, request=httpx.Request("GET", "http://test"))
    with patch("httpx.AsyncClient.get", return_value=mock_resp):
        # Ready
        rep_ready = await run_ollama_diagnostics("http://localhost:11434", requested_model="qwen2.5:1.5b")
        assert rep_ready.reachable is True
        assert rep_ready.connectivity_state == "ready"
        assert rep_ready.model_ready is True

        # Missing
        rep_missing = await run_ollama_diagnostics("http://localhost:11434", requested_model="mistral:7b")
        assert rep_missing.reachable is True
        assert rep_missing.connectivity_state == "requested_model_missing"
        assert rep_missing.model_ready is False
        assert "ollama pull mistral:7b" in (rep_missing.remediation_hint or "")


@pytest.mark.asyncio
async def test_ollama_diagnostics_reachable_general() -> None:
    # State 1: Reachable general
    mock_resp = httpx.Response(200, json={"models": [{"name": "llama3.2:3b"}]}, request=httpx.Request("GET", "http://test"))
    with patch("httpx.AsyncClient.get", return_value=mock_resp):
        rep = await run_ollama_diagnostics("http://localhost:11434")
        assert rep.reachable is True
        assert rep.connectivity_state == "reachable"
        assert rep.installed_models_count == 1
