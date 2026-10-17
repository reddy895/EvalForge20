"""Google Gemini provider adapter supporting generateContent REST API and token usage."""

import time
from typing import Any

import httpx

from app.config import get_settings
from app.domain.contracts import ProviderRequest, ProviderResponse
from app.domain.errors import NormalizedErrorCategory
from app.providers.base import BaseProvider
from app.providers.registry import provider_registry

KNOWN_GEMINI_MODELS = [
    "gemini-1.5-flash",
    "gemini-1.5-pro",
    "gemini-2.0-flash",
    "gemini-1.5-flash-8b",
]


class GeminiProvider(BaseProvider):
    """Provider adapter communicating with Google Gemini REST API."""

    def __init__(
        self,
        model_identifier: str = "gemini-1.5-flash",
        base_url: str | None = None,
        api_key: str | None = None,
        timeout_seconds: float = 60.0,
        **kwargs: Any,
    ):
        settings = get_settings()
        self.base_url = (base_url or settings.gemini_base_url).rstrip("/")
        self.api_key = api_key or (
            settings.gemini_api_key.get_secret_value() if settings.gemini_api_key else None
        )
        super().__init__(provider_name="gemini", timeout_seconds=timeout_seconds)
        self.model_identifier = model_identifier

    async def health_check(self) -> bool:
        """Verify API key configuration and connectivity to Gemini."""
        if not self.api_key:
            return False
        try:
            url = f"{self.base_url}/models?key={self.api_key}"
            async with httpx.AsyncClient(timeout=3.0) as client:
                resp = await client.get(url)
                return resp.status_code == 200
        except Exception:
            return False

    async def list_models(self) -> list[str]:
        """Return available Gemini model identifiers."""
        if not self.api_key:
            return KNOWN_GEMINI_MODELS

        try:
            url = f"{self.base_url}/models?key={self.api_key}"
            async with httpx.AsyncClient(timeout=4.0) as client:
                resp = await client.get(url)
                if resp.status_code == 200:
                    data = resp.json()
                    models = [
                        m["name"].replace("models/", "")
                        for m in data.get("models", [])
                        if "generateContent" in m.get("supportedGenerationMethods", [])
                    ]
                    return sorted(models) if models else KNOWN_GEMINI_MODELS
        except Exception:
            pass
        return KNOWN_GEMINI_MODELS

    async def generate(self, request: ProviderRequest) -> ProviderResponse:
        """Send prompt to Gemini generateContent REST endpoint."""
        if not self.api_key:
            return ProviderResponse(
                output_text=None,
                latency_ms=0.0,
                error_category=NormalizedErrorCategory.AUTHENTICATION_ERROR.value,
                error_message="Google Gemini API key not configured. Set EVALFORGE20_GEMINI_API_KEY or GEMINI_API_KEY environment variable.",
                is_success=False,
            )

        async def _call_gemini() -> ProviderResponse:
            start_time = time.perf_counter()
            model_slug = self.model_identifier.replace("models/", "")
            url = f"{self.base_url}/models/{model_slug}:generateContent?key={self.api_key}"

            contents: list[dict[str, Any]] = [
                {
                    "role": "user",
                    "parts": [{"text": request.prompt}],
                }
            ]

            generation_config: dict[str, Any] = {}
            if request.temperature is not None:
                generation_config["temperature"] = request.temperature
            if request.max_tokens:
                generation_config["maxOutputTokens"] = request.max_tokens
            if request.response_format == "json":
                generation_config["responseMimeType"] = "application/json"

            payload: dict[str, Any] = {
                "contents": contents,
                "generationConfig": generation_config,
            }

            if request.system_prompt:
                payload["systemInstruction"] = {
                    "parts": [{"text": request.system_prompt}],
                }

            payload.update(request.extra_params)

            try:
                async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                    resp = await client.post(url, json=payload)
                    resp.raise_for_status()
                    data = resp.json()
            except httpx.HTTPStatusError as exc:
                elapsed_ms = round((time.perf_counter() - start_time) * 1000.0, 2)
                status = exc.response.status_code
                cat = NormalizedErrorCategory.EXECUTION_ERROR
                if status in (400, 401, 403):
                    cat = NormalizedErrorCategory.AUTHENTICATION_ERROR
                elif status == 429:
                    cat = NormalizedErrorCategory.RATE_LIMIT

                return ProviderResponse(
                    output_text=None,
                    latency_ms=elapsed_ms,
                    error_category=cat.value,
                    error_message=f"Gemini HTTP {status} error: {exc.response.text[:200]}",
                    is_success=False,
                )

            elapsed_ms = round((time.perf_counter() - start_time) * 1000.0, 2)
            candidates = data.get("candidates", [])
            output_text = ""
            if candidates:
                parts = candidates[0].get("content", {}).get("parts", [])
                for p in parts:
                    if "text" in p:
                        output_text += p["text"]

            usage_meta = data.get("usageMetadata", {})
            raw_usage = {
                "prompt_tokens": usage_meta.get("promptTokenCount"),
                "completion_tokens": usage_meta.get("candidatesTokenCount"),
                "total_tokens": usage_meta.get("totalTokenCount"),
            }

            return ProviderResponse(
                output_text=output_text,
                latency_ms=elapsed_ms,
                token_usage=raw_usage,
                raw_response=data,
                is_success=True,
            )

        return await self.execute_with_guard(request, _call_gemini)


provider_registry.register("gemini", GeminiProvider)
provider_registry.register("google", GeminiProvider)
