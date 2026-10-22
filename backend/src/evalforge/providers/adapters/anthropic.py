"""Anthropic Claude inference provider adapter."""

import time
from typing import Any

import httpx

from src.evalforge.core.config import get_settings
from src.evalforge.core.errors import ModelNotFoundError, ProviderError
from src.evalforge.core.logging import get_logger
from src.evalforge.providers.base import BaseProvider
from src.evalforge.providers.schemas import (
    BenchmarkScoreItem,
    InferenceRequest,
    InferenceResponse,
    ModelInfo,
    ModelPricingItem,
    ProviderCapabilities,
    TokenUsage,
    ToolCall,
)

logger = get_logger("evalforge.providers.anthropic")


def get_anthropic_models() -> list[ModelInfo]:
    return [
        ModelInfo(
            id="anthropic:claude-3-5-sonnet-20241022",
            name="Claude 3.5 Sonnet",
            provider="anthropic",
            model_identifier="claude-3-5-sonnet-20241022",
            family="Claude",
            parameter_count="Large frontier",
            context_window=200000,
            modalities=["text->text", "image->text"],
            supports_tools=True,
            supports_structured_output=True,
            license="Commercial Proprietary",
            is_commercial_use_allowed=True,
            release_date="2024-10-22",
            description="Industry-leading frontier reasoning and code synthesis model with 200k context window and computer use.",
            is_local=False,
            is_installed=False,
            is_remote=True,
            benchmarks=[
                BenchmarkScoreItem(benchmark_name="HumanEval", metric="pass@1", score=93.7, source="Anthropic Claude 3.5 Sonnet Card", verified=True),
                BenchmarkScoreItem(benchmark_name="MMLU", metric="accuracy", score=88.7, source="Anthropic Claude 3.5 Sonnet Card", verified=True),
                BenchmarkScoreItem(benchmark_name="GSM8K", metric="accuracy", score=96.4, source="Anthropic Claude 3.5 Sonnet Card", verified=True),
            ],
            pricing=ModelPricingItem(input_cost_per_m=3.00, output_cost_per_m=15.00, currency="USD", is_free_local=False, source_url="https://anthropic.com/pricing"),
            strengths=["State of the art coding and agentic reasoning", "Massive 200k context window", "Detailed analytical writing"],
            weaknesses=["Higher output token pricing", "Cloud service availability dependency"],
            recommended_tasks=["coding", "agent", "reasoning", "complex_analysis"],
        ),
        ModelInfo(
            id="anthropic:claude-3-5-haiku-20241022",
            name="Claude 3.5 Haiku",
            provider="anthropic",
            model_identifier="claude-3-5-haiku-20241022",
            family="Claude",
            parameter_count="Fast compact",
            context_window=200000,
            modalities=["text->text"],
            supports_tools=True,
            supports_structured_output=True,
            license="Commercial Proprietary",
            is_commercial_use_allowed=True,
            release_date="2024-10-22",
            description="Ultra-fast intelligence at near-instant latency matching previous generation frontier performance.",
            is_local=False,
            is_installed=False,
            is_remote=True,
            benchmarks=[
                BenchmarkScoreItem(benchmark_name="HumanEval", metric="pass@1", score=75.9, source="Anthropic Technical Card", verified=True),
                BenchmarkScoreItem(benchmark_name="MMLU", metric="accuracy", score=81.2, source="Anthropic Technical Card", verified=True),
            ],
            pricing=ModelPricingItem(input_cost_per_m=0.80, output_cost_per_m=4.00, currency="USD", is_free_local=False, source_url="https://anthropic.com/pricing"),
            strengths=["Blazing speed", "200k context", "Sub-second first-token latency"],
            weaknesses=["Output token cost higher than GPT-4o mini"],
            recommended_tasks=["low_latency", "structured_json", "agent_monitoring"],
        ),
    ]


class AnthropicProvider(BaseProvider):
    """Anthropic Claude Messages API adapter."""

    def __init__(self, api_key: str | None = None) -> None:
        settings = get_settings()
        self.api_key = api_key if api_key is not None else settings.ANTHROPIC_API_KEY
        self.base_url = settings.ANTHROPIC_BASE_URL.rstrip("/")
        self.timeout_seconds = settings.PROVIDER_TIMEOUT_SECONDS
        super().__init__(
            name="anthropic",
            config={"base_url": self.base_url, "has_api_key": bool(self.api_key)},
            display_name="Anthropic Claude",
            provider_type="cloud",
            implementation_status="configurable_cloud",
            setup_instructions="Set ANTHROPIC_API_KEY in your .env file or environment variables to enable live Claude evaluation.",
        )
        self._client: httpx.AsyncClient | None = None

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key and len(self.api_key.strip()) > 0)

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            headers = {
                "x-api-key": self.api_key or "",
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            }
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(self.timeout_seconds, connect=10.0),
                headers=headers,
            )
        return self._client

    async def health_check(self) -> bool:
        if not self.is_configured:
            return False
        # Minimal check or ping
        return True

    async def list_models(self) -> list[ModelInfo]:
        return get_anthropic_models()

    async def get_model_capabilities(self, model_id: str) -> ProviderCapabilities:
        return ProviderCapabilities(
            supports_chat=True,
            supports_generation=True,
            supports_streaming=True,
            supports_tools=True,
            supports_structured_output=True,
            supports_system_prompt=True,
            max_context_length=200000,
        )

    async def generate(self, request: InferenceRequest) -> InferenceResponse:
        if not self.is_configured:
            raise ProviderError(
                f"Provider 'anthropic' is not configured with an API key. {self.setup_instructions}",
                provider="anthropic",
            )

        start_time = time.perf_counter()
        client = await self._get_client()

        target_model = request.model
        if ":" in target_model and target_model.startswith("anthropic:"):
            target_model = target_model.split(":", 1)[1]

        messages: list[dict[str, Any]] = []
        if request.messages:
            for m in request.messages:
                messages.append({"role": m.role if m.role in ("user", "assistant") else "user", "content": m.content})
        elif request.prompt:
            messages.append({"role": "user", "content": request.prompt})

        payload: dict[str, Any] = {
            "model": target_model,
            "messages": messages,
            "max_tokens": request.max_tokens or 4096,
            "temperature": request.temperature,
        }
        if request.system_prompt:
            payload["system"] = request.system_prompt

        # Tool calling schema
        if request.tools:
            payload["tools"] = [
                {
                    "name": t.name,
                    "description": t.description,
                    "input_schema": t.parameters,
                }
                for t in request.tools
            ]

        url = f"{self.base_url}/messages"
        try:
            resp = await client.post(url, json=payload)
            if resp.status_code == 200:
                data = resp.json()
                content_blocks = data.get("content", [])
                text_parts = []
                tool_calls: list[ToolCall] | None = None

                for b in content_blocks:
                    if b.get("type") == "text":
                        text_parts.append(b.get("text", ""))
                    elif b.get("type") == "tool_use":
                        if tool_calls is None:
                            tool_calls = []
                        tool_calls.append(ToolCall(name=b.get("name", "unknown"), arguments=b.get("input", {})))

                usage_data = data.get("usage", {})
                usage = TokenUsage(
                    prompt_tokens=usage_data.get("input_tokens"),
                    completion_tokens=usage_data.get("output_tokens"),
                    total_tokens=(usage_data.get("input_tokens", 0) + usage_data.get("output_tokens", 0)),
                )

                duration_ms = (time.perf_counter() - start_time) * 1000
                return InferenceResponse(
                    text="".join(text_parts),
                    model=request.model,
                    provider="anthropic",
                    latency_ms=round(duration_ms, 2),
                    usage=usage,
                    tool_calls=tool_calls,
                    raw_metadata={"id": data.get("id"), "stop_reason": data.get("stop_reason")},
                )
            if resp.status_code == 404:
                raise ModelNotFoundError(request.model, "anthropic")
            raise ProviderError(f"Anthropic API returned HTTP {resp.status_code}: {resp.text[:250]}", provider="anthropic")
        except (ModelNotFoundError, ProviderError):
            raise
        except Exception as exc:
            raise ProviderError(f"Anthropic error: {exc}", provider="anthropic") from exc

    async def close(self) -> None:
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None
