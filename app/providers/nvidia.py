"""NVIDIA NIM provider adapter supporting hosted models and custom endpoints."""

import time
from typing import Any

import httpx

from app.config import get_settings
from app.domain.contracts import ProviderRequest, ProviderResponse
from app.domain.errors import NormalizedErrorCategory
from app.providers.base import BaseProvider
from app.providers.registry import provider_registry

KNOWN_NVIDIA_MODELS = [
    "meta/llama-3.1-70b-instruct",
    "meta/llama-3.1-8b-instruct",
    "meta/llama-3.3-70b-instruct",
    "mistralai/mistral-large-2-instruct",
    "nvidia/nemotron-4-340b-instruct",
]


class NvidiaProvider(BaseProvider):
    """Provider adapter communicating with NVIDIA hosted endpoints / NIM API."""

    def __init__(
        self,
        model_identifier: str = "meta/llama-3.1-8b-instruct",
        base_url: str | None = None,
        api_key: str | None = None,
        timeout_seconds: float = 60.0,
        **kwargs: Any,
    ):
        settings = get_settings()
        self.base_url = (base_url or settings.nvidia_base_url).rstrip("/")
        self.api_key = api_key or (
            settings.nvidia_api_key.get_secret_value() if settings.nvidia_api_key else None
        )
        super().__init__(provider_name="nvidia", timeout_seconds=timeout_seconds)
        self.model_identifier = model_identifier

    async def health_check(self) -> bool:
        """Verify API key configuration and connectivity to NVIDIA API."""
        if not self.api_key:
            return False
        try:
            headers = {"Authorization": f"Bearer {self.api_key}"}
            async with httpx.AsyncClient(timeout=3.0) as client:
                resp = await client.get(f"{self.base_url}/models", headers=headers)
                return resp.status_code == 200
        except Exception:
            return False

    async def list_models(self) -> list[str]:
        """Fetch model identifiers available from NVIDIA endpoint or return verified defaults."""
        if not self.api_key:
            return KNOWN_NVIDIA_MODELS

        try:
            headers = {"Authorization": f"Bearer {self.api_key}"}
            async with httpx.AsyncClient(timeout=4.0) as client:
                resp = await client.get(f"{self.base_url}/models", headers=headers)
                if resp.status_code == 200:
                    data = resp.json()
                    models = [m["id"] for m in data.get("data", []) if "id" in m]
                    return sorted(models) if models else KNOWN_NVIDIA_MODELS
        except Exception:
            pass
        return KNOWN_NVIDIA_MODELS

    async def generate(self, request: ProviderRequest) -> ProviderResponse:
        """Send chat completion prompt to NVIDIA NIM endpoint."""
        if not self.api_key:
            return ProviderResponse(
                output_text=None,
                latency_ms=0.0,
                error_category=NormalizedErrorCategory.AUTHENTICATION_ERROR.value,
                error_message="NVIDIA API key not configured. Set EVALFORGE20_NVIDIA_API_KEY or NVIDIA_API_KEY environment variable.",
                is_success=False,
            )

        async def _call_nvidia() -> ProviderResponse:
            start_time = time.perf_counter()
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }

            messages: list[dict[str, Any]] = []
            if request.system_prompt:
                messages.append({"role": "system", "content": request.system_prompt})
            messages.append({"role": "user", "content": request.prompt})

            payload: dict[str, Any] = {
                "model": self.model_identifier,
                "messages": messages,
                "temperature": request.temperature if request.temperature is not None else 0.0,
            }

            if request.max_tokens:
                payload["max_tokens"] = request.max_tokens
            if request.response_format == "json":
                payload["response_format"] = {"type": "json_object"}

            payload.update(request.extra_params)

            try:
                async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                    resp = await client.post(
                        f"{self.base_url}/chat/completions",
                        headers=headers,
                        json=payload,
                    )
                    resp.raise_for_status()
                    data = resp.json()
            except httpx.HTTPStatusError as exc:
                elapsed_ms = round((time.perf_counter() - start_time) * 1000.0, 2)
                status = exc.response.status_code
                cat = NormalizedErrorCategory.EXECUTION_ERROR
                if status in (401, 403):
                    cat = NormalizedErrorCategory.AUTHENTICATION_ERROR
                elif status == 429:
                    cat = NormalizedErrorCategory.RATE_LIMIT

                return ProviderResponse(
                    output_text=None,
                    latency_ms=elapsed_ms,
                    error_category=cat.value,
                    error_message=f"NVIDIA HTTP {status} error: {exc.response.text[:200]}",
                    is_success=False,
                )

            elapsed_ms = round((time.perf_counter() - start_time) * 1000.0, 2)
            choices = data.get("choices", [])
            output_text = choices[0]["message"]["content"] if choices else ""
            raw_usage = data.get("usage", {})

            return ProviderResponse(
                output_text=output_text,
                latency_ms=elapsed_ms,
                token_usage=raw_usage,
                raw_response=data,
                is_success=True,
            )

        return await self.execute_with_guard(request, _call_nvidia)


provider_registry.register("nvidia", NvidiaProvider)
