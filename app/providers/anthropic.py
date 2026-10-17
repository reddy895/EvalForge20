"""Anthropic provider adapter supporting Messages API and token tracking."""

import time
from typing import Any

import httpx

from app.config import get_settings
from app.domain.contracts import ProviderRequest, ProviderResponse
from app.domain.errors import NormalizedErrorCategory
from app.providers.base import BaseProvider
from app.providers.registry import provider_registry

KNOWN_ANTHROPIC_MODELS = [
    "claude-3-5-sonnet-20241022",
    "claude-3-5-haiku-20241022",
    "claude-3-opus-20240229",
    "claude-3-sonnet-20240229",
    "claude-3-haiku-20240307",
]


class AnthropicProvider(BaseProvider):
    """Provider adapter communicating with Anthropic Messages API."""

    def __init__(
        self,
        model_identifier: str = "claude-3-5-haiku-20241022",
        base_url: str | None = None,
        api_key: str | None = None,
        timeout_seconds: float = 60.0,
        **kwargs: Any,
    ):
        settings = get_settings()
        self.base_url = (base_url or settings.anthropic_base_url).rstrip("/")
        self.api_key = api_key or (
            settings.anthropic_api_key.get_secret_value() if settings.anthropic_api_key else None
        )
        super().__init__(provider_name="anthropic", timeout_seconds=timeout_seconds)
        self.model_identifier = model_identifier

    async def health_check(self) -> bool:
        """Verify API key configuration and connectivity to Anthropic."""
        if not self.api_key:
            return False
        try:
            headers = {
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
            }
            async with httpx.AsyncClient(timeout=3.0) as client:
                resp = await client.get(f"{self.base_url}/models", headers=headers)
                return resp.status_code in (200, 404, 405)
        except Exception:
            return False

    async def list_models(self) -> list[str]:
        """Return verified Claude model identifiers."""
        if not self.api_key:
            return KNOWN_ANTHROPIC_MODELS

        try:
            headers = {
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
            }
            async with httpx.AsyncClient(timeout=4.0) as client:
                resp = await client.get(f"{self.base_url}/models", headers=headers)
                if resp.status_code == 200:
                    data = resp.json()
                    models = [m["id"] for m in data.get("data", []) if "id" in m]
                    return sorted(models) if models else KNOWN_ANTHROPIC_MODELS
        except Exception:
            pass
        return KNOWN_ANTHROPIC_MODELS

    async def generate(self, request: ProviderRequest) -> ProviderResponse:
        """Send message prompt to Anthropic API."""
        if not self.api_key:
            return ProviderResponse(
                output_text=None,
                latency_ms=0.0,
                error_category=NormalizedErrorCategory.AUTHENTICATION_ERROR.value,
                error_message="Anthropic API key not configured. Set EVALFORGE20_ANTHROPIC_API_KEY or ANTHROPIC_API_KEY environment variable.",
                is_success=False,
            )

        async def _call_anthropic() -> ProviderResponse:
            start_time = time.perf_counter()
            headers = {
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
                "Content-Type": "application/json",
            }

            payload: dict[str, Any] = {
                "model": self.model_identifier,
                "messages": [{"role": "user", "content": request.prompt}],
                "max_tokens": request.max_tokens or 4096,
            }

            if request.system_prompt:
                payload["system"] = request.system_prompt

            if request.temperature is not None:
                payload["temperature"] = request.temperature

            payload.update(request.extra_params)

            try:
                async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                    resp = await client.post(
                        f"{self.base_url}/messages",
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
                    error_message=f"Anthropic HTTP {status} error: {exc.response.text[:200]}",
                    is_success=False,
                )

            elapsed_ms = round((time.perf_counter() - start_time) * 1000.0, 2)
            content_blocks = data.get("content", [])
            output_text = ""
            for block in content_blocks:
                if block.get("type") == "text":
                    output_text += block.get("text", "")

            usage = data.get("usage", {})
            raw_usage = {
                "prompt_tokens": usage.get("input_tokens"),
                "completion_tokens": usage.get("output_tokens"),
            }

            return ProviderResponse(
                output_text=output_text,
                latency_ms=elapsed_ms,
                token_usage=raw_usage,
                raw_response=data,
                is_success=True,
            )

        return await self.execute_with_guard(request, _call_anthropic)


provider_registry.register("anthropic", AnthropicProvider)
