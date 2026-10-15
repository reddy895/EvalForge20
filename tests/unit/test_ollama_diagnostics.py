"""Unit tests for Ollama configuration, reachability diagnostics, and setup guidance."""

import httpx
import pytest
from app.config import Settings
from app.providers.ollama_diagnostics import (
    diagnose_ollama,
    get_ollama_setup_instructions,
)


def test_ollama_config_environment_aliases(monkeypatch):
    """Verify that OLLAMA_ environment variables override default settings."""
    monkeypatch.setenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
    monkeypatch.setenv("OLLAMA_MODEL", "llama3.2:3b")
    monkeypatch.setenv("OLLAMA_TIMEOUT_SECONDS", "45.0")

    settings = Settings()
    assert settings.ollama_base_url == "http://127.0.0.1:11434"
    assert settings.ollama_model == "llama3.2:3b"
    assert settings.ollama_timeout_seconds == 45.0


def test_ollama_setup_instructions_content():
    """Verify setup instructions contain actionable terminal commands."""
    instructions = get_ollama_setup_instructions("http://localhost:11434")
    assert len(instructions) >= 3
    assert any("curl -fsSL https://ollama.com/install.sh" in s for s in instructions)
    assert any("ollama serve" in s for s in instructions)
    assert any("ollama pull" in s for s in instructions)


@pytest.mark.asyncio
async def test_diagnose_ollama_reachable(monkeypatch):
    """Verify diagnostic report when Ollama server is running and returns model list."""

    async def mock_get(self, url, **kwargs):
        return httpx.Response(
            status_code=200,
            json={"models": [{"name": "qwen2.5:3b"}, {"name": "llama3.2:3b"}]},
            request=httpx.Request("GET", url),
        )

    monkeypatch.setattr(httpx.AsyncClient, "get", mock_get)

    report = await diagnose_ollama("http://localhost:11434")
    assert report.is_reachable is True
    assert "qwen2.5:3b" in report.installed_models
    assert "llama3.2:3b" in report.installed_models
    assert report.error_message is None
    assert len(report.setup_instructions) == 0


@pytest.mark.asyncio
async def test_diagnose_ollama_offline_connect_error(monkeypatch):
    """Verify diagnostic report and guidance when Ollama server is offline."""

    async def mock_get(self, url, **kwargs):
        raise httpx.ConnectError("Connection refused")

    monkeypatch.setattr(httpx.AsyncClient, "get", mock_get)

    report = await diagnose_ollama("http://localhost:11434")
    assert report.is_reachable is False
    assert len(report.installed_models) == 0
    assert "Cannot connect to Ollama server" in (report.error_message or "")
    assert len(report.setup_instructions) > 0


@pytest.mark.asyncio
async def test_diagnose_ollama_timeout(monkeypatch):
    """Verify diagnostic report when Ollama server connection times out."""

    async def mock_get(self, url, **kwargs):
        raise httpx.TimeoutException("Timed out")

    monkeypatch.setattr(httpx.AsyncClient, "get", mock_get)

    report = await diagnose_ollama("http://localhost:11434", timeout_seconds=1.0)
    assert report.is_reachable is False
    assert "timed out" in (report.error_message or "")
