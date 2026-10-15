"""Diagnostic utilities and installation guidance for the local Ollama daemon."""

from typing import Any

import httpx
from pydantic import BaseModel, ConfigDict, Field


class OllamaDiagnosticReport(BaseModel):
    """Detailed health and availability status of the local Ollama instance."""

    model_config = ConfigDict(frozen=True)

    is_reachable: bool = Field(..., description="Whether the Ollama HTTP server is responsive")
    base_url: str = Field(..., description="Target Ollama endpoint URL")
    installed_models: list[str] = Field(
        default_factory=list, description="Models currently available locally"
    )
    status_code: int | None = Field(
        default=None, description="HTTP response code from health probe"
    )
    error_message: str | None = Field(
        default=None, description="Connection error details if unreachable"
    )
    setup_instructions: list[str] = Field(
        default_factory=list, description="Actionable setup steps"
    )


def get_ollama_setup_instructions(base_url: str = "http://localhost:11434") -> list[str]:
    """Return actionable guidance for installing and launching Ollama locally."""
    return [
        "1. Install Ollama: run 'curl -fsSL https://ollama.com/install.sh | sh' (Linux/macOS) or visit https://ollama.com/download",
        f"2. Start the Ollama server: run 'ollama serve' and ensure it listens on {base_url}",
        "3. Download your preferred model: run 'ollama pull qwen2.5:3b' (or llama3.2:3b, mistral:7b, etc.)",
        "4. Verify availability: run 'ollama list' or 'evalforge20 provider check ollama'",
    ]


async def diagnose_ollama(
    base_url: str = "http://localhost:11434",
    timeout_seconds: float = 3.0,
) -> OllamaDiagnosticReport:
    """Probe the Ollama server and return diagnostic status with model inventory and instructions."""
    clean_url = base_url.rstrip("/")
    tags_endpoint = f"{clean_url}/api/tags"

    try:
        async with httpx.AsyncClient(timeout=timeout_seconds) as client:
            resp = await client.get(tags_endpoint)
            if resp.status_code == 200:
                data: dict[str, Any] = resp.json()
                raw_models = data.get("models", [])
                models = [str(m.get("name", "")) for m in raw_models if m.get("name")]
                return OllamaDiagnosticReport(
                    is_reachable=True,
                    base_url=base_url,
                    installed_models=models,
                    status_code=resp.status_code,
                    error_message=None,
                    setup_instructions=[],
                )
            else:
                return OllamaDiagnosticReport(
                    is_reachable=False,
                    base_url=base_url,
                    installed_models=[],
                    status_code=resp.status_code,
                    error_message=f"Ollama server returned unexpected HTTP status {resp.status_code}",
                    setup_instructions=get_ollama_setup_instructions(base_url),
                )
    except httpx.ConnectError:
        return OllamaDiagnosticReport(
            is_reachable=False,
            base_url=base_url,
            installed_models=[],
            status_code=None,
            error_message=f"Cannot connect to Ollama server at {base_url}. Service is not running or unreachable.",
            setup_instructions=get_ollama_setup_instructions(base_url),
        )
    except httpx.TimeoutException:
        return OllamaDiagnosticReport(
            is_reachable=False,
            base_url=base_url,
            installed_models=[],
            status_code=None,
            error_message=f"Connection to Ollama at {base_url} timed out after {timeout_seconds}s.",
            setup_instructions=get_ollama_setup_instructions(base_url),
        )
    except Exception as exc:
        return OllamaDiagnosticReport(
            is_reachable=False,
            base_url=base_url,
            installed_models=[],
            status_code=None,
            error_message=f"Unexpected error probing Ollama: {exc}",
            setup_instructions=get_ollama_setup_instructions(base_url),
        )


# Convenient alias
check_ollama_status = diagnose_ollama

