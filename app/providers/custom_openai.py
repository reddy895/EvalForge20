"""Generic OpenAI-compatible provider adapter supporting arbitrary endpoints (vLLM, LM Studio, OpenRouter, etc.)."""

import time
from typing import Any

import httpx

from app.domain.contracts import ProviderRequest, ProviderResponse
from app.domain.errors import NormalizedErrorCategory
from app.providers.base import BaseProvider
from app.providers.registry import provider_registry


class CustomOpenAIProvider(BaseProvider):
    """Provider adapter communicating with any OpenAI-compatible API endpoint."""

    def __init__(
        self,
        model_identifier: str = "custom-model",
        base_url: str = "http://localhost:8000/v1",
        api_key: str | None = None,
        timeout_seconds: float = 60.0,
        extra_headers: dict[str, str] | None = None,
        **kwargs: Any,
    ):
        self.base_url = (base_url or "http://localhost:8000/v1").rstrip("/")
        self.api_key = api_key or ""
        self.extra_headers = extra_headers or {}
        super().__init__(provider_name="custom_openai", timeout_seconds=timeout_seconds)
        self.model_identifier = model_identifier

    def _get_headers(self) -> dict[str, str]:
        headers: dict[str, str] = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        headers.update(self.extra_headers)
        return headers

    async def health_check(self) -> bool:
        """Verify connectivity to custom OpenAI-compatible endpoint."""
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                resp = await client.get(f"{self.base_url}/models", headers=self._get_headers())
                return resp.status_code == 200
        except Exception:
            return False

    async def list_models(self) -> list[str]:
        """Fetch model identifiers available from the custom endpoint."""
        try:
            async with httpx.AsyncClient(timeout=4.0) as client:
                resp = await client.get(f"{self.base_url}/models", headers=self._get_headers())
                if resp.status_code == 200:
                    data = resp.json()
                    models = [m["id"] for m in data.get("data", []) if "id" in m]
                    if models:
                        return sorted(models)
        except Exception:
            pass
        return [self.model_identifier]

    async def generate(self, request: ProviderRequest) -> ProviderResponse:
        """Send chat completion prompt to the custom OpenAI-compatible endpoint."""

        async def _call_endpoint() -> ProviderResponse:
            start_time = time.perf_counter()
            headers = self._get_headers()

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
                    error_message=f"HTTP {status} error: {exc.response.text[:200]}",
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

        return await self.execute_with_guard(request, _call_endpoint)


provider_registry.register("custom_openai", CustomOpenAIProvider)
