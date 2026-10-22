"""Generic OpenAI-compatible inference provider adapter."""

import asyncio
import json
import time
from typing import Any

import httpx

from src.evalforge.core.errors import ModelNotFoundError, ProviderConnectionError, ProviderError
from src.evalforge.core.logging import get_logger
from src.evalforge.providers.base import BaseProvider
from src.evalforge.providers.schemas import (
    InferenceRequest,
    InferenceResponse,
    ModelInfo,
    ProviderCapabilities,
    TokenUsage,
    ToolCall,
)

logger = get_logger("evalforge.providers.openai_compatible")


class OpenAICompatibleProvider(BaseProvider):
    """Generic adapter for OpenAI-compatible REST APIs (vLLM, LMStudio, LocalAI, Together, etc.)."""

    def __init__(
        self,
        name: str = "openai_compatible",
        base_url: str = "http://localhost:8080/v1",
        api_key: str | None = None,
        display_name: str = "OpenAI Compatible",
        provider_type: str = "cloud",
        implementation_status: str = "implemented_and_tested",
        setup_instructions: str | None = None,
        default_models: list[ModelInfo] | None = None,
        timeout_seconds: float = 60.0,
        extra_headers: dict[str, str] | None = None,
    ):
        config = {
            "base_url": base_url.rstrip("/"),
            "has_api_key": bool(api_key),
        }
        super().__init__(
            name=name,
            config=config,
            display_name=display_name,
            provider_type=provider_type,
            implementation_status=implementation_status,
            setup_instructions=setup_instructions
            or f"Configure endpoint URL ({base_url}) and optionally set API key in settings or environment.",
        )
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout_seconds = timeout_seconds
        self.default_models = default_models or []
        self.extra_headers = extra_headers or {}
        self._client: httpx.AsyncClient | None = None

    @property
    def is_configured(self) -> bool:
        # If it's a cloud service expecting an API key, check if key is set
        if self.provider_type == "cloud" and not self.name.startswith("mock"):
            return bool(self.api_key and len(self.api_key.strip()) > 0)
        return True

    def _get_headers(self) -> dict[str, str]:
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "EvalForge20/2.0.0",
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        headers.update(self.extra_headers)
        return headers

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(self.timeout_seconds, connect=10.0),
                headers=self._get_headers(),
            )
        return self._client

    async def health_check(self) -> bool:
        if not self.is_configured:
            return False
        try:
            client = await self._get_client()
            url = f"{self.base_url}/models"
            resp = await client.get(url, timeout=5.0)
            return resp.status_code in (200, 201)
        except Exception as exc:
            logger.debug("Health check failed for %s at %s: %s", self.name, self.base_url, exc)
            return False

    async def list_models(self) -> list[ModelInfo]:
        """Discover models via GET /models endpoint when reachable; merge with defaults."""
        discovered: list[ModelInfo] = []
        if self.is_configured:
            try:
                client = await self._get_client()
                url = f"{self.base_url}/models"
                resp = await client.get(url, timeout=8.0)
                if resp.status_code == 200:
                    data = resp.json()
                    raw_list = data.get("data", []) if isinstance(data, dict) else data
                    for item in raw_list:
                        m_id = item.get("id") if isinstance(item, dict) else str(item)
                        if m_id:
                            discovered.append(
                                ModelInfo(
                                    id=f"{self.name}:{m_id}" if not m_id.startswith(f"{self.name}:") else m_id,
                                    name=m_id,
                                    provider=self.name,
                                    model_identifier=m_id,
                                    is_local=self.provider_type == "local",
                                    is_installed=True,
                                    is_remote=self.provider_type == "cloud",
                                    description=f"Discovered dynamically from {self.display_name} API.",
                                )
                            )
            except Exception as exc:
                logger.debug("Dynamic model discovery error for %s: %s", self.name, exc)

        if discovered:
            # Merge with default models if any
            existing_ids = {m.name for m in discovered}
            for dm in self.default_models:
                if dm.name not in existing_ids:
                    discovered.append(dm)
            return discovered

        return list(self.default_models)

    async def get_model_capabilities(self, model_id: str) -> ProviderCapabilities:
        return ProviderCapabilities(
            supports_chat=True,
            supports_generation=True,
            supports_streaming=True,
            supports_tools=True,
            supports_structured_output=True,
            supports_system_prompt=True,
            max_context_length=128000,
        )

    async def generate(self, request: InferenceRequest) -> InferenceResponse:
        if not self.is_configured:
            raise ProviderError(
                f"Provider '{self.name}' is not configured with a valid API key. {self.setup_instructions}",
                provider=self.name,
            )

        start_time = time.perf_counter()
        client = await self._get_client()

        # Build messages payload
        messages: list[dict[str, Any]] = []
        if request.system_prompt:
            messages.append({"role": "system", "content": request.system_prompt})
        if request.messages:
            for msg in request.messages:
                messages.append({"role": msg.role, "content": msg.content})
        elif request.prompt:
            messages.append({"role": "user", "content": request.prompt})

        # Strip provider prefix if present
        target_model = request.model
        if ":" in target_model and target_model.startswith(f"{self.name}:"):
            target_model = target_model.split(":", 1)[1]

        body: dict[str, Any] = {
            "model": target_model,
            "messages": messages,
            "temperature": request.temperature,
        }
        if request.max_tokens is not None:
            body["max_tokens"] = request.max_tokens
        if request.top_p is not None:
            body["top_p"] = request.top_p
        if request.stop:
            body["stop"] = request.stop

        # Structured output format
        if request.json_schema:
            body["response_format"] = {
                "type": "json_schema",
                "json_schema": {
                    "name": "schema_response",
                    "strict": True,
                    "schema": request.json_schema,
                },
            }

        # Tool calling format
        if request.tools:
            body["tools"] = [
                {
                    "type": "function",
                    "function": {
                        "name": t.name,
                        "description": t.description,
                        "parameters": t.parameters,
                    },
                }
                for t in request.tools
            ]

        url = f"{self.base_url}/chat/completions"
        retries = 2
        last_error: Exception | None = None

        for attempt in range(retries + 1):
            try:
                resp = await client.post(url, json=body)
                if resp.status_code == 200:
                    data = resp.json()
                    choices = data.get("choices", [])
                    if not choices:
                        raise ProviderError("Empty choices returned from model", provider=self.name)

                    choice = choices[0]
                    message = choice.get("message", {})
                    response_text = message.get("content") or ""

                    # Extract tool calls
                    tool_calls: list[ToolCall] | None = None
                    raw_tc = message.get("tool_calls", [])
                    if raw_tc:
                        tool_calls = []
                        for tc in raw_tc:
                            fn = tc.get("function", {})
                            fn_name = fn.get("name", "unknown")
                            fn_args = fn.get("arguments", {})
                            if isinstance(fn_args, str):
                                try:
                                    fn_args = json.loads(fn_args)
                                except Exception:
                                    fn_args = {"raw": fn_args}
                            tool_calls.append(ToolCall(name=fn_name, arguments=fn_args))

                    usage_data = data.get("usage") or {}
                    usage = None
                    if usage_data:
                        usage = TokenUsage(
                            prompt_tokens=usage_data.get("prompt_tokens"),
                            completion_tokens=usage_data.get("completion_tokens"),
                            total_tokens=usage_data.get("total_tokens"),
                        )

                    duration_ms = (time.perf_counter() - start_time) * 1000
                    return InferenceResponse(
                        text=response_text,
                        model=request.model,
                        provider=self.name,
                        latency_ms=round(duration_ms, 2),
                        usage=usage,
                        tool_calls=tool_calls,
                        raw_metadata={
                            "id": data.get("id"),
                            "model": data.get("model"),
                            "system_fingerprint": data.get("system_fingerprint"),
                        },
                    )

                if resp.status_code == 404:
                    raise ModelNotFoundError(request.model, self.name)
                elif resp.status_code in (401, 403):
                    raise ProviderError(
                        f"Authentication failed for {self.name} (HTTP {resp.status_code}). Check your API key. {resp.text[:200]}",
                        provider=self.name,
                    )
                elif resp.status_code == 429:
                    if attempt < retries:
                        await asyncio.sleep(1.0 * (attempt + 1))
                        continue
                    raise ProviderError(f"Rate limit exceeded on {self.name}: {resp.text[:200]}", provider=self.name)
                else:
                    raise ProviderError(
                        f"Inference request failed with HTTP {resp.status_code}: {resp.text[:300]}",
                        provider=self.name,
                    )

            except (httpx.ConnectError, httpx.ConnectTimeout) as exc:
                last_error = ProviderConnectionError(
                    f"Could not connect to {self.name} at {self.base_url}: {exc}",
                    provider=self.name,
                    base_url=self.base_url,
                )
                if attempt < retries:
                    await asyncio.sleep(0.5)
                    continue
                raise last_error from exc
            except (ModelNotFoundError, ProviderError):
                raise
            except Exception as exc:
                last_error = exc
                if attempt < retries:
                    await asyncio.sleep(0.5)
                    continue
                raise ProviderError(f"Unexpected error communicating with {self.name}: {exc}", provider=self.name) from exc

        raise ProviderError(f"Failed to generate after retries: {last_error}", provider=self.name)

    async def close(self) -> None:
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None
