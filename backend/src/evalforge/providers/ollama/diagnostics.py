"""Ollama connectivity probe, 8-state diagnosis, and setup advisor."""

import os
import shutil
from dataclasses import dataclass, field
from datetime import UTC, datetime

import httpx


@dataclass
class OllamaDiagnosticReport:
    """Detailed health and connectivity report covering 8 distinct lifecycle states."""

    reachable: bool
    connectivity_state: str  # reachable, installed_not_running, connection_refused, timeout, reachable_no_models, requested_model_missing, ready, invalid_config
    base_url: str
    version: str | None = None
    installed_locally: bool = False
    installed_models_count: int = 0
    available_models: list[str] = field(default_factory=list)
    model_ready: bool = False
    error_message: str | None = None
    remediation_hint: str | None = None
    last_checked_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())


def _normalize_model_name(name: str) -> str:
    """Strip tags and leading/trailing whitespace for robust model matching."""
    clean = name.strip().lower()
    return clean[:-7] if clean.endswith(":latest") else clean


async def run_ollama_diagnostics(
    base_url: str = "http://localhost:11434",
    requested_model: str | None = None,
    timeout: float = 3.0,
) -> OllamaDiagnosticReport:
    """Probe Ollama HTTP endpoint and classify into one of 8 distinct connectivity states."""
    now_iso = datetime.now(UTC).isoformat()
    clean_url = (base_url or "").strip().rstrip("/")
    installed_locally = bool(shutil.which("ollama"))
    is_local_host = any(h in clean_url.lower() for h in ("localhost", "127.0.0.1", "0.0.0.0", "::1"))

    # State 8: Invalid configuration / unsupported endpoint
    if not clean_url.startswith(("http://", "https://")):
        return OllamaDiagnosticReport(
            reachable=False,
            connectivity_state="invalid_config",
            base_url=clean_url,
            installed_locally=installed_locally,
            error_message="Invalid URL scheme. Must begin with http:// or https://",
            remediation_hint="Verify OLLAMA_BASE_URL configuration in .env.",
            last_checked_at=now_iso,
        )

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            try:
                resp = await client.get(f"{clean_url}/api/tags")
            except httpx.ConnectTimeout as exc:
                # State 4: Connection timeout
                return OllamaDiagnosticReport(
                    reachable=False,
                    connectivity_state="timeout",
                    base_url=clean_url,
                    installed_locally=installed_locally,
                    error_message=f"Request to {clean_url} timed out after {timeout}s: {exc}",
                    remediation_hint="Ollama server took too long to respond. Check host connectivity or server load.",
                    last_checked_at=now_iso,
                )
            except (httpx.ConnectError, ConnectionRefusedError) as exc:
                if installed_locally and is_local_host:
                    # State 2: Installed locally but not running
                    return OllamaDiagnosticReport(
                        reachable=False,
                        connectivity_state="installed_not_running",
                        base_url=clean_url,
                        installed_locally=True,
                        error_message=f"Connection refused at {clean_url}: {exc}",
                        remediation_hint="Ollama is installed locally, but the service is stopped. Run 'ollama serve' to start it.",
                        last_checked_at=now_iso,
                    )
                # State 3: Connection refused / service unreachable
                return OllamaDiagnosticReport(
                    reachable=False,
                    connectivity_state="connection_refused",
                    base_url=clean_url,
                    installed_locally=False,
                    error_message=f"Connection refused at {clean_url}: {exc}",
                    remediation_hint=f"Ollama daemon not reachable at {clean_url}. Start daemon or install from https://ollama.com.",
                    last_checked_at=now_iso,
                )

            if resp.status_code != 200:
                # State 8: Invalid configuration / unsupported endpoint
                hint = (
                    f"Ollama endpoint {clean_url}/api/tags returned 404. Ensure your server is a compatible Ollama instance."
                    if resp.status_code == 404
                    else (
                        f"Ollama daemon returned internal server error HTTP {resp.status_code}. Check daemon logs."
                        if resp.status_code >= 500
                        else f"Verify that {clean_url} points to an authentic Ollama REST API instance."
                    )
                )
                return OllamaDiagnosticReport(
                    reachable=False,
                    connectivity_state="invalid_config",
                    base_url=clean_url,
                    installed_locally=installed_locally,
                    error_message=f"Endpoint returned HTTP {resp.status_code}",
                    remediation_hint=hint,
                    last_checked_at=now_iso,
                )

            # Successfully reached Ollama daemon
            try:
                data = resp.json()
            except Exception as exc:
                return OllamaDiagnosticReport(
                    reachable=False,
                    connectivity_state="invalid_config",
                    base_url=clean_url,
                    installed_locally=installed_locally,
                    error_message=f"Malformed JSON response: {exc}",
                    remediation_hint="Ollama endpoint returned non-JSON payload.",
                    last_checked_at=now_iso,
                )

            # Probe version
            version: str | None = None
            try:
                v_resp = await client.get(f"{clean_url}/api/version", timeout=2.0)
                if v_resp.status_code == 200:
                    version = v_resp.json().get("version")
            except Exception:
                version = "unknown"

            raw_models = data.get("models", [])
            available_models: list[str] = [
                m.get("name") or m.get("model") for m in raw_models if (m.get("name") or m.get("model"))
            ]
            model_count = len(available_models)

            # State 5: Ollama reachable but no models installed
            if model_count == 0:
                return OllamaDiagnosticReport(
                    reachable=True,
                    connectivity_state="reachable_no_models",
                    base_url=clean_url,
                    version=version,
                    installed_locally=installed_locally,
                    installed_models_count=0,
                    available_models=[],
                    error_message="No models currently installed in Ollama.",
                    remediation_hint="Run 'ollama pull llama3.2:3b' or 'ollama pull qwen2.5:1.5b' to download a model.",
                    last_checked_at=now_iso,
                )

            # Check requested model readiness if specified
            if requested_model:
                norm_req = _normalize_model_name(requested_model)
                is_present = any(
                    _normalize_model_name(m) == norm_req
                    or m.lower().startswith(norm_req)
                    or norm_req.startswith(_normalize_model_name(m))
                    for m in available_models
                )
                if is_present:
                    # State 7: Model available and ready for inference
                    return OllamaDiagnosticReport(
                        reachable=True,
                        connectivity_state="ready",
                        base_url=clean_url,
                        version=version,
                        installed_locally=installed_locally,
                        installed_models_count=model_count,
                        available_models=available_models,
                        model_ready=True,
                        remediation_hint=f"Model '{requested_model}' is installed and ready for evaluation.",
                        last_checked_at=now_iso,
                    )
                # State 6: Ollama reachable but the requested model is missing
                return OllamaDiagnosticReport(
                    reachable=True,
                    connectivity_state="requested_model_missing",
                    base_url=clean_url,
                    version=version,
                    installed_locally=installed_locally,
                    installed_models_count=model_count,
                    available_models=available_models,
                    model_ready=False,
                    error_message=f"Model '{requested_model}' is not present in local Ollama repository.",
                    remediation_hint=f"Run 'ollama pull {requested_model}' to install this model before starting evaluation.",
                    last_checked_at=now_iso,
                )

            # State 1: Ollama reachable with models installed
            return OllamaDiagnosticReport(
                reachable=True,
                connectivity_state="reachable",
                base_url=clean_url,
                version=version,
                installed_locally=installed_locally,
                installed_models_count=model_count,
                available_models=available_models,
                model_ready=True,
                remediation_hint=f"Ollama is reachable with {model_count} models installed.",
                last_checked_at=now_iso,
            )

    except Exception as exc:
        return OllamaDiagnosticReport(
            reachable=False,
            connectivity_state="connection_refused",
            base_url=clean_url,
            installed_locally=installed_locally,
            error_message=str(exc),
            remediation_hint="Ollama daemon error. Check service logs or restart via 'ollama serve'.",
            last_checked_at=now_iso,
        )
