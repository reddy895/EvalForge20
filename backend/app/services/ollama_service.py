"""Dedicated Ollama client for health checks, model discovery, and inference."""

import time
from typing import Any

import httpx
from backend.app.core.config import get_settings
from backend.app.core.errors import ErrorCode, EvalForgeError
from backend.app.core.logging import get_logger
from backend.app.schemas.models import OllamaStatusReport

logger = get_logger("ollama_service")


class OllamaService:
    """Interacts with local Ollama daemon via its HTTP API."""

    def __init__(self, base_url: str | None = None, timeout_seconds: float = 60.0):
        settings = get_settings()
        self.base_url = (base_url or settings.ollama_base_url).rstrip("/")
        self.timeout = timeout_seconds

    async def get_status(self) -> OllamaStatusReport:
        """Perform real health check and discover installed models."""
        start_time = time.perf_counter()
        instructions = [
            "1. Install Ollama: run 'curl -fsSL https://ollama.com/install.sh | sh' or visit https://ollama.com/download",
            "2. Start the daemon: run 'ollama serve' (default port 11434)",
            "3. Pull a model: run 'ollama pull qwen2.5:3b' or use the UI Model Explorer",
            "4. Verify daemon: run 'ollama list'",
        ]

        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                resp = await client.get(f"{self.base_url}/api/tags")
                latency_ms = round((time.perf_counter() - start_time) * 1000.0, 2)

                if resp.status_code == 200:
                    data = resp.json()
                    models = [m["name"] for m in data.get("models", []) if "name" in m]
                    status_label = "online" if models else "no_models_installed"

                    # Get version if available
                    version = None
                    try:
                        v_resp = await client.get(f"{self.base_url}/api/version")
                        if v_resp.status_code == 200:
                            version = v_resp.json().get("version")
                    except Exception:
                        pass

                    return OllamaStatusReport(
                        is_reachable=True,
                        base_url=self.base_url,
                        version=version,
                        installed_models=models,
                        models_count=len(models),
                        status_label=status_label,
                        latency_ms=latency_ms,
                        setup_instructions=instructions,
                    )
                else:
                    return OllamaStatusReport(
                        is_reachable=False,
                        base_url=self.base_url,
                        status_label="offline",
                        latency_ms=latency_ms,
                        error_message=f"Ollama returned HTTP status {resp.status_code}",
                        setup_instructions=instructions,
                    )
        except httpx.ConnectError:
            latency_ms = round((time.perf_counter() - start_time) * 1000.0, 2)
            return OllamaStatusReport(
                is_reachable=False,
                base_url=self.base_url,
                status_label="offline",
                latency_ms=latency_ms,
                error_message=f"Connection refused at {self.base_url}. Service is not running.",
                setup_instructions=instructions,
            )
        except httpx.TimeoutException:
            latency_ms = round((time.perf_counter() - start_time) * 1000.0, 2)
            return OllamaStatusReport(
                is_reachable=False,
                base_url=self.base_url,
                status_label="timeout",
                latency_ms=latency_ms,
                error_message=f"Connection to Ollama at {self.base_url} timed out.",
                setup_instructions=instructions,
            )
        except Exception as exc:
            latency_ms = round((time.perf_counter() - start_time) * 1000.0, 2)
            return OllamaStatusReport(
                is_reachable=False,
                base_url=self.base_url,
                status_label="offline",
                latency_ms=latency_ms,
                error_message=f"Failed to reach Ollama: {exc}",
                setup_instructions=instructions,
            )

    async def pull_model(self, model_name: str) -> dict[str, Any]:
        """Trigger explicit download/pull of an Ollama model."""
        tag = model_name.strip()
        if not tag:
            raise EvalForgeError("Model name cannot be empty.", ErrorCode.VALIDATION_ERROR)

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(
                    f"{self.base_url}/api/pull",
                    json={"name": tag, "stream": False},
                )
                if resp.status_code == 200:
                    return {
                        "model": tag,
                        "status": "initiated",
                        "message": f"Successfully pulled '{tag}'.",
                    }
                else:
                    err_msg = resp.text
                    raise EvalForgeError(
                        f"Ollama model pull returned {resp.status_code}: {err_msg}",
                        ErrorCode.OLLAMA_UNREACHABLE,
                    )
        except httpx.ConnectError:
            raise EvalForgeError(
                f"Cannot connect to Ollama at {self.base_url} to pull '{tag}'.",
                ErrorCode.OLLAMA_UNREACHABLE,
            ) from None
        except Exception as exc:
            raise EvalForgeError(
                f"Error pulling model '{tag}': {exc}", ErrorCode.INFERENCE_FAILED
            ) from exc

    async def generate(self, model: str, prompt: str, temperature: float = 0.0) -> dict[str, Any]:
        """Execute real inference against an installed Ollama model (with deterministic mock for offline test verification)."""
        if model in ["mock-model-v1", "deterministic-mock-v1"]:
            start_time = time.perf_counter()
            p_lower = prompt.lower()
            if "def reverse_string" in p_lower:
                out = "def reverse_string(s: str) -> str:\n    return s[::-1]"
            elif "def is_palindrome" in p_lower:
                out = "def is_palindrome(s: str) -> bool:\n    clean = s.lower().replace(' ', '')\n    return clean == clean[::-1]"
            elif "def fibonacci" in p_lower:
                out = "def fibonacci(n: int) -> int:\n    if n <= 0: return 0\n    if n == 1: return 1\n    a, b = 0, 1\n    for _ in range(2, n + 1):\n        a, b = b, a + b\n    return b"
            elif "extract the name, age, and role in valid json" in p_lower:
                out = '{"name": "Alice", "age": 28, "role": "Engineer"}'
            elif "json array" in p_lower:
                out = '["apple", "banana", "cherry"]'
            elif "25 * 14" in p_lower or "25*14" in p_lower:
                out = "The product of 25 and 14 is 350."
            elif "perimeter" in p_lower:
                out = "The perimeter of a rectangle with length 12 and width 7 is 2 * (12 + 7) = 38."
            else:
                out = f"Deterministic response to: {prompt[:50]}"
            latency_ms = round((time.perf_counter() - start_time) * 1000.0 + 4.5, 2)
            p_toks = len(prompt.split())
            c_toks = len(out.split())
            return {
                "output": out,
                "latency_ms": latency_ms,
                "tokens": {
                    "prompt_tokens": p_toks,
                    "completion_tokens": c_toks,
                    "total_tokens": p_toks + c_toks,
                },
                "is_success": True,
            }

        start_time = time.perf_counter()
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                payload = {
                    "model": model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": temperature,
                    },
                }
                resp = await client.post(f"{self.base_url}/api/generate", json=payload)
                latency_ms = round((time.perf_counter() - start_time) * 1000.0, 2)

                if resp.status_code == 200:
                    data = resp.json()
                    response_text = data.get("response", "")
                    prompt_tokens = data.get("prompt_eval_count", 0)
                    eval_tokens = data.get("eval_count", 0)
                    return {
                        "output": response_text,
                        "latency_ms": latency_ms,
                        "tokens": {
                            "prompt_tokens": prompt_tokens,
                            "completion_tokens": eval_tokens,
                            "total_tokens": prompt_tokens + eval_tokens,
                        },
                        "is_success": True,
                    }
                elif resp.status_code == 404:
                    raise EvalForgeError(
                        f"Model '{model}' is not installed in local Ollama daemon. Run 'ollama pull {model}'.",
                        ErrorCode.MODEL_NOT_FOUND,
                    )
                else:
                    raise EvalForgeError(
                        f"Ollama generation failed (HTTP {resp.status_code}): {resp.text}",
                        ErrorCode.INFERENCE_FAILED,
                    )
        except httpx.ConnectError:
            raise EvalForgeError(
                f"Cannot connect to Ollama at {self.base_url}. Daemon is offline.",
                ErrorCode.OLLAMA_UNREACHABLE,
            ) from None
        except httpx.TimeoutException:
            raise EvalForgeError(
                f"Ollama generation timed out after {self.timeout}s for model '{model}'.",
                ErrorCode.EXECUTION_TIMEOUT,
            ) from None
