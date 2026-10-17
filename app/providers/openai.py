"""OpenAI provider adapter supporting Chat Completions and model discovery."""

import time
from typing import Any

import httpx

from app.config import get_settings
from app.domain.contracts import ProviderRequest, ProviderResponse
from app.domain.errors import NormalizedErrorCategory
from app.providers.base import BaseProvider
from app.providers.registry import provider_registry

KNOWN_OPENAI_MODELS = [
    "gpt-4o",
    "gpt-4o-mini",
    "o1",
    "o1-mini",
    "o3-mini",
    "gpt-4-turbo",
    "gpt-3.5-turbo",
]


class OpenAIProvider(BaseProvider):
    """Provider adapter communicating with OpenAI Chat Completions API."""

    def __init__(
        self,
        model_identifier: str = "gpt-4o-mini",
        base_url: str | None = None,
        api_key: str | None = None,
        timeout_seconds: float = 60.0,
        **kwargs: Any,
    ):
        settings = get_settings()
        self.base_url = (base_url or settings.openai_base_url).rstrip("/")
        self.api_key = api_key or (
            settings.openai_api_key.get_secret_value() if settings.openai_api_key else None
        )
        super().__init__(provider_name="openai", timeout_seconds=timeout_seconds)
        self.model_identifier = model_identifier

    async def health_check(self) -> bool:
        """Verify API key configuration and connectivity to OpenAI."""
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
        """Fetch model identifiers available from OpenAI or return verified defaults."""
        if not self.api_key:
            return KNOWN_OPENAI_MODELS

        try:
            headers = {"Authorization": f"Bearer {self.api_key}"}
            async with httpx.AsyncClient(timeout=4.0) as client:
                resp = await client.get(f"{self.base_url}/models", headers=headers)
                if resp.status_code == 200:
                    data = resp.json()
                    models = [
                        m["id"]
                        for m in data.get("data", [])
                        if m.get("id", "").startswith(("gpt-", "o1", "o3"))
                    ]
                    return sorted(models) if models else KNOWN_OPENAI_MODELS
        except Exception:
            pass
        return KNOWN_OPENAI_MODELS

    async def generate(self, request: ProviderRequest) -> ProviderResponse:
        """Send chat completion prompt to OpenAI API."""
        if not self.api_key:
            return ProviderResponse(
                output_text=None,
                latency_ms=0.0,
                error_category=NormalizedErrorCategory.AUTHENTICATION_ERROR.value,
                error_message="OpenAI API key not configured. Set EVALFORGE20_OPENAI_API_KEY or OPENAI_API_KEY environment variable.",
                is_success=False,
            )

        async def _call_openai() -> ProviderResponse:
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
            }

            # Sampling options (only set temperature if not o1/o3 reasoning model)
            if not self.model_identifier.startswith(("o1", "o3")):
                payload["temperature"] = (
                    request.temperature if request.temperature is not None else 0.0
                )

            if request.max_tokens:
                if self.model_identifier.startswith(("o1", "o3")):
                    payload["max_completion_tokens"] = request.max_tokens
                else:
                    payload["max_tokens"] = request.max_tokens

            if request.response_format == "json":
                payload["response_format"] = {"type": "json_object"}

            if request.tools:
                payload["tools"] = request.tools

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
                    error_message=f"OpenAI HTTP {status} error: {exc.response.text[:200]}",
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

        return await self.execute_with_guard(request, _call_openai)


provider_registry.register("openai", OpenAIProvider)
