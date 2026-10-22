"""Ollama connectivity probe and setup advisor."""

import httpx
from dataclasses import dataclass

@dataclass
class OllamaDiagnosticReport:
    reachable: bool
    base_url: str
    version: str | None
    installed_models_count: int
    error_message: str | None
    remediation_hint: str | None

async def run_ollama_diagnostics(base_url: str = "http://localhost:11434") -> OllamaDiagnosticReport:
    """Probe Ollama HTTP endpoint and provide actionable remediation guidance."""
    clean_url = base_url.rstrip("/")
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.get(f"{clean_url}/api/tags")
            if resp.status_code == 200:
                data = resp.json()
                models = data.get("models", [])
                return OllamaDiagnosticReport(
                    reachable=True,
                    base_url=clean_url,
                    version="0.3+",
                    installed_models_count=len(models),
                    error_message=None,
                    remediation_hint=None,
                )
            return OllamaDiagnosticReport(
                reachable=False,
                base_url=clean_url,
                version=None,
                installed_models_count=0,
                error_message=f"HTTP {resp.status_code}",
                remediation_hint="Check if Ollama daemon is running properly.",
            )
    except Exception as exc:
        return OllamaDiagnosticReport(
            reachable=False,
            base_url=clean_url,
            version=None,
            installed_models_count=0,
            error_message=str(exc),
            remediation_hint="Ollama not detected. Start with 'ollama serve' or install from https://ollama.com.",
        )
