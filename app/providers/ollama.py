"""Local model provider adapter for Ollama."""

import time
from typing import Any

import httpx
from pydantic import BaseModel, ConfigDict, Field

from app.config import get_settings
from app.domain.contracts import ProviderRequest, ProviderResponse
from app.domain.errors import NormalizedErrorCategory
from app.providers.base import BaseProvider
from app.providers.registry import provider_registry


class OllamaModelDetails(BaseModel):
    """Detailed metadata for a locally installed Ollama model."""

    model_config = ConfigDict(frozen=True)

    name: str = Field(..., description="Model tag name, e.g. 'qwen2.5:3b'")
    model: str = Field(default="", description="Model identifier")
    size: int = Field(default=0, description="Size on disk in bytes")
    size_bytes: int = Field(default=0, description="Size on disk in bytes (alias)")
    digest: str = Field(default="", description="Model digest hash")
    parameter_size: str | None = Field(
        default=None, description="Reported parameter size, e.g. '3.1B'"
    )
    quantization_level: str | None = Field(
        default=None, description="Quantization format, e.g. 'Q4_K_M'"
    )
    family: str | None = Field(default=None, description="Model family, e.g. 'qwen2'")
    modified_at: str | None = Field(default=None, description="ISO timestamp of last update")
    details: dict[str, Any] = Field(default_factory=dict, description="Raw details dictionary")


class OllamaProvider(BaseProvider):
    """Local inference provider communicating with Ollama HTTP API."""

    def __init__(
        self,
        model_identifier: str = "qwen2.5:3b",
        base_url: str | None = None,
        timeout_seconds: float | None = None,
        **kwargs: Any,
    ):
        settings = get_settings()
        self.base_url = (base_url or settings.ollama_base_url).rstrip("/")
        timeout = timeout_seconds or settings.ollama_timeout_seconds
        super().__init__(provider_name="ollama", timeout_seconds=timeout)
        self.model_identifier = model_identifier

    async def health_check(self) -> bool:
        """Check if local Ollama daemon is reachable and responding."""
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                resp = await client.get(f"{self.base_url}/api/tags")
                return resp.status_code == 200
        except Exception:
            return False

    async def list_models(self) -> list[str]:
        """Fetch list of model tag names currently available in local Ollama instance."""
        details = await self.list_detailed_models()
        return [m.name for m in details]

    async def list_detailed_models(self) -> list[OllamaModelDetails]:
        """Fetch detailed model specifications from local Ollama daemon."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(f"{self.base_url}/api/tags")
                if resp.status_code == 200:
                    data = resp.json()
                    results: list[OllamaModelDetails] = []
                    for item in data.get("models", []):
                        details_meta = item.get("details", {})
                        size_val = int(item.get("size", 0))
                        name_val = item.get("name", "unknown")
                        results.append(
                            OllamaModelDetails(
                                name=name_val,
                                model=item.get("model", name_val),
                                size=size_val,
                                size_bytes=size_val,
                                digest=item.get("digest", ""),
                                parameter_size=details_meta.get("parameter_size"),
                                quantization_level=details_meta.get("quantization_level"),
                                family=details_meta.get("family"),
                                modified_at=item.get("modified_at"),
                                details=details_meta,
                            )
                        )
                    return results
        except Exception:
            pass
        return []

    async def generate(self, request: ProviderRequest) -> ProviderResponse:
        """Send prompt to Ollama /api/generate endpoint."""

        async def _call_ollama() -> ProviderResponse:
            start_time = time.perf_counter()

            # Context window & sampling options
            settings = get_settings()
            num_ctx = (
                request.extra_params.get("num_ctx")
                or request.extra_params.get("context_length")
                or settings.ollama_context_length
            )
            temp = (
                request.temperature
                if request.temperature is not None
                else settings.ollama_temperature
            )

            options_payload: dict[str, Any] = {
                "temperature": temp,
                "num_ctx": num_ctx,
            }
            if request.max_tokens:
                options_payload["num_predict"] = request.max_tokens
            if request.stop_sequences:
                options_payload["stop"] = request.stop_sequences
            for param in ("top_k", "top_p", "repeat_penalty", "seed"):
                if param in request.extra_params:
                    options_payload[param] = request.extra_params[param]
            options_payload.update(request.extra_params.get("options", {}))

            payload: dict[str, Any] = {
                "model": self.model_identifier,
                "prompt": request.prompt,
                "stream": False,
                "options": options_payload,
            }
            if request.system_prompt:
                payload["system"] = request.system_prompt
            if request.response_format == "json":
                payload["format"] = "json"

            try:
                async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                    resp = await client.post(f"{self.base_url}/api/generate", json=payload)
                    if resp.status_code == 404 or (
                        "not found" in resp.text.lower() and "model" in resp.text.lower()
                    ):
                        elapsed_ms = round((time.perf_counter() - start_time) * 1000.0, 2)
                        return ProviderResponse(
                            output_text=None,
                            latency_ms=elapsed_ms,
                            error_category=NormalizedErrorCategory.PROVIDER_UNAVAILABLE.value,
                            error_message=(
                                f"Model '{self.model_identifier}' is not installed in local Ollama. "
                                f"Run 'ollama pull {self.model_identifier}' in your terminal to install it."
                            ),
                            is_success=False,
                        )
                    resp.raise_for_status()
                    data = resp.json()
            except httpx.ConnectError:
                elapsed_ms = round((time.perf_counter() - start_time) * 1000.0, 2)
                return ProviderResponse(
                    output_text=None,
                    latency_ms=elapsed_ms,
                    error_category=NormalizedErrorCategory.PROVIDER_UNAVAILABLE.value,
                    error_message=(
                        f"Cannot connect to Ollama daemon at '{self.base_url}'. "
                        "Ensure the server is running with 'ollama serve'."
                    ),
                    is_success=False,
                )
            except httpx.TimeoutException:
                elapsed_ms = round((time.perf_counter() - start_time) * 1000.0, 2)
                return ProviderResponse(
                    output_text=None,
                    latency_ms=elapsed_ms,
                    error_category=NormalizedErrorCategory.TIMEOUT.value,
                    error_message=(
                        f"Inference request for model '{self.model_identifier}' timed out after {self.timeout_seconds}s. "
                        "If running a large model or cold-starting GPU weights, increase timeout in settings."
                    ),
                    is_success=False,
                )

            elapsed_ms = round((time.perf_counter() - start_time) * 1000.0, 2)
            output_text = data.get("response", "")

            # Extract token counts
            raw_usage = {
                "prompt_eval_count": data.get("prompt_eval_count"),
                "eval_count": data.get("eval_count"),
            }

            return ProviderResponse(
                output_text=output_text,
                latency_ms=elapsed_ms,
                token_usage=raw_usage,
                raw_response=data,
                is_success=True,
            )

        return await self.execute_with_guard(request, _call_ollama)


provider_registry.register("ollama", OllamaProvider)
