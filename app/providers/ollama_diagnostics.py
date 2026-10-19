"""Diagnostic utilities and installation guidance for the local Ollama daemon."""

import time
from typing import Any

import httpx
from pydantic import BaseModel, ConfigDict, Field, computed_field


class OllamaDiagnosticReport(BaseModel):
    """Detailed health and availability status of the local Ollama instance."""

    model_config = ConfigDict(frozen=True)

    is_reachable: bool = Field(..., description="Whether the Ollama HTTP server is responsive")
    base_url: str = Field(..., description="Target Ollama endpoint URL")
    version: str | None = Field(default=None, description="Ollama daemon version from /api/version")
    installed_models: list[str] = Field(
        default_factory=list, description="Models currently available locally"
    )
    status_code: int | None = Field(
        default=None, description="HTTP response code from health probe"
    )
    latency_ms: float | None = Field(default=None, description="Probe round-trip latency in ms")
    error_message: str | None = Field(
        default=None, description="Connection error details if unreachable"
    )
    setup_instructions: list[str] = Field(
        default_factory=list, description="Actionable setup steps"
    )

    @computed_field  # type: ignore[prop-decorator]
    @property
    def connected(self) -> bool:
        """Serialized alias for is_reachable -- consumed by frontend status indicator."""
        return self.is_reachable

    @computed_field  # type: ignore[prop-decorator]
    @property
    def models(self) -> list[str]:
        """Serialized alias for installed_models -- consumed by frontend model picker."""
        return self.installed_models

    @computed_field  # type: ignore[prop-decorator]
    @property
    def models_count(self) -> int:
        """Serialized count of locally installed models."""
        return len(self.installed_models)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def status_label(self) -> str:
        """Human-readable status label: online | no_models_installed | offline."""
        if not self.is_reachable:
            return "offline"
        if not self.installed_models:
            return "no_models_installed"
        return "online"


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
    start_time = time.perf_counter()
    clean_url = base_url.rstrip("/")
    tags_endpoint = f"{clean_url}/api/tags"
    version_endpoint = f"{clean_url}/api/version"

    try:
        async with httpx.AsyncClient(timeout=timeout_seconds) as client:
            resp = await client.get(tags_endpoint)
            elapsed_ms = round((time.perf_counter() - start_time) * 1000.0, 2)
            if resp.status_code == 200:
                data: dict[str, Any] = resp.json()
                raw_models = data.get("models", [])
                models = [str(m.get("name", "")) for m in raw_models if m.get("name")]

                # Fetch version string if available
                version_val: str | None = None
                try:
                    v_resp = await client.get(version_endpoint)
                    if v_resp.status_code == 200:
                        version_val = v_resp.json().get("version")
                except Exception:
                    pass

                return OllamaDiagnosticReport(
                    is_reachable=True,
                    base_url=base_url,
                    version=version_val,
                    installed_models=models,
                    status_code=resp.status_code,
                    latency_ms=elapsed_ms,
                    error_message=None,
                    setup_instructions=[],
                )
            else:
                return OllamaDiagnosticReport(
                    is_reachable=False,
                    base_url=base_url,
                    version=None,
                    installed_models=[],
                    status_code=resp.status_code,
                    latency_ms=elapsed_ms,
                    error_message=f"Ollama server returned unexpected HTTP status {resp.status_code}",
                    setup_instructions=get_ollama_setup_instructions(base_url),
                )
    except httpx.ConnectError:
        elapsed_ms = round((time.perf_counter() - start_time) * 1000.0, 2)
        return OllamaDiagnosticReport(
            is_reachable=False,
            base_url=base_url,
            version=None,
            installed_models=[],
            status_code=None,
            latency_ms=elapsed_ms,
            error_message=f"Cannot connect to Ollama server at {base_url}. Service is not running or unreachable.",
            setup_instructions=get_ollama_setup_instructions(base_url),
        )
    except httpx.TimeoutException:
        elapsed_ms = round((time.perf_counter() - start_time) * 1000.0, 2)
        return OllamaDiagnosticReport(
            is_reachable=False,
            base_url=base_url,
            version=None,
            installed_models=[],
            status_code=None,
            latency_ms=elapsed_ms,
            error_message=f"Connection to Ollama at {base_url} timed out after {timeout_seconds}s.",
            setup_instructions=get_ollama_setup_instructions(base_url),
        )
    except Exception as exc:
        elapsed_ms = round((time.perf_counter() - start_time) * 1000.0, 2)
        return OllamaDiagnosticReport(
            is_reachable=False,
            base_url=base_url,
            version=None,
            installed_models=[],
            status_code=None,
            latency_ms=elapsed_ms,
            error_message=f"Unexpected error probing Ollama: {exc}",
            setup_instructions=get_ollama_setup_instructions(base_url),
        )


# Convenient alias used throughout the codebase
check_ollama_status = diagnose_ollama
