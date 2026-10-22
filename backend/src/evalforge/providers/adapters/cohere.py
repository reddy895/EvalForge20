"""Cohere inference provider adapter."""

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
)

logger = get_logger("evalforge.providers.cohere")


def get_cohere_models() -> list[ModelInfo]:
    return [
        ModelInfo(
            id="cohere:command-r-plus-08-2024",
            name="Command R+ (08-2024)",
            provider="cohere",
            model_identifier="command-r-plus-08-2024",
            family="Command",
            parameter_count="104B",
            context_window=128000,
            modalities=["text->text"],
            supports_tools=True,
            supports_structured_output=True,
            license="Cohere Commercial",
            is_commercial_use_allowed=True,
            release_date="2024-08-01",
            description="Enterprise RAG and multi-step tool-use specialist model with advanced citation grounding and multilingual support.",
            is_local=False,
            is_installed=False,
            is_remote=True,
            benchmarks=[
                BenchmarkScoreItem(benchmark_name="MMLU", metric="accuracy", score=75.7, source="Cohere Command R+ Tech Report", verified=True),
                BenchmarkScoreItem(benchmark_name="HumanEval", metric="pass@1", score=68.9, source="Cohere Command R+ Tech Report", verified=True),
            ],
            pricing=ModelPricingItem(input_cost_per_m=2.50, output_cost_per_m=10.00, currency="USD", is_free_local=False, source_url="https://cohere.com/pricing"),
            strengths=["Grounded citation generation", "Enterprise RAG precision", "128k context"],
            weaknesses=["Higher cost for large output generation"],
            recommended_tasks=["rag", "tool_use", "enterprise_search", "citations"],
        ),
        ModelInfo(
            id="cohere:command-r-08-2024",
            name="Command R (08-2024)",
            provider="cohere",
            model_identifier="command-r-08-2024",
            family="Command",
            parameter_count="35B",
            context_window=128000,
            modalities=["text->text"],
            supports_tools=True,
            supports_structured_output=True,
            license="Cohere Commercial",
            is_commercial_use_allowed=True,
            release_date="2024-08-01",
            description="Scalable enterprise workhorse model optimized for conversational interactions and RAG pipelines.",
            is_local=False,
            is_installed=False,
            is_remote=True,
            benchmarks=[
                BenchmarkScoreItem(benchmark_name="MMLU", metric="accuracy", score=68.2, source="Cohere Tech Report", verified=True),
            ],
            pricing=ModelPricingItem(input_cost_per_m=0.15, output_cost_per_m=0.60, currency="USD", is_free_local=False, source_url="https://cohere.com/pricing"),
            strengths=["Affordable high-throughput enterprise RAG", "128k context"],
            weaknesses=["Lower reasoning depth on intricate coding"],
            recommended_tasks=["rag", "chat", "summarization"],
        ),
    ]


class CohereProvider(BaseProvider):
    """Cohere v2 Chat API adapter."""

    def __init__(self) -> None:
        settings = get_settings()
        self.api_key = settings.COHERE_API_KEY
        self.base_url = settings.COHERE_BASE_URL.rstrip("/")
        self.timeout_seconds = settings.PROVIDER_TIMEOUT_SECONDS
        super().__init__(
            name="cohere",
            config={"base_url": self.base_url, "has_api_key": bool(self.api_key)},
            display_name="Cohere",
            provider_type="cloud",
            implementation_status="configurable_cloud",
            setup_instructions="Set COHERE_API_KEY in your .env file or environment variables to enable live Cohere evaluations.",
        )
        self._client: httpx.AsyncClient | None = None

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key and len(self.api_key.strip()) > 0)

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "User-Agent": "EvalForge20/2.0.0",
            }
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(self.timeout_seconds, connect=10.0),
                headers=headers,
            )
        return self._client

    async def health_check(self) -> bool:
        if not self.is_configured:
            return False
        return True

    async def list_models(self) -> list[ModelInfo]:
        return get_cohere_models()

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
                f"Provider 'cohere' is not configured with an API key. {self.setup_instructions}",
                provider="cohere",
            )

        start_time = time.perf_counter()
        client = await self._get_client()

        target_model = request.model
        if ":" in target_model and target_model.startswith("cohere:"):
            target_model = target_model.split(":", 1)[1]

        messages: list[dict[str, Any]] = []
        if request.messages:
            for m in request.messages:
                messages.append({"role": m.role, "content": m.content})
        elif request.prompt:
            messages.append({"role": "user", "content": request.prompt})

        payload: dict[str, Any] = {
            "model": target_model,
            "messages": messages,
            "temperature": request.temperature,
        }
        if request.max_tokens:
            payload["max_tokens"] = request.max_tokens

        url = f"{self.base_url}/chat"
        try:
            resp = await client.post(url, json=payload)
            if resp.status_code == 200:
                data = resp.json()
                message = data.get("message", {})
                content_list = message.get("content", [])
                text_parts = [c.get("text", "") for c in content_list if c.get("type") == "text"]

                usage_meta = data.get("usage", {}).get("billed_units", {})
                usage = TokenUsage(
                    prompt_tokens=usage_meta.get("input_tokens"),
                    completion_tokens=usage_meta.get("output_tokens"),
                    total_tokens=(usage_meta.get("input_tokens", 0) + usage_meta.get("output_tokens", 0)),
                )

                duration_ms = (time.perf_counter() - start_time) * 1000
                return InferenceResponse(
                    text="".join(text_parts),
                    model=request.model,
                    provider="cohere",
                    latency_ms=round(duration_ms, 2),
                    usage=usage,
                    tool_calls=None,
                    raw_metadata={"id": data.get("id")},
                )
            if resp.status_code == 404:
                raise ModelNotFoundError(request.model, "cohere")
            raise ProviderError(f"Cohere API returned HTTP {resp.status_code}: {resp.text[:250]}", provider="cohere")
        except (ModelNotFoundError, ProviderError):
            raise
        except Exception as exc:
            raise ProviderError(f"Cohere error: {exc}", provider="cohere") from exc

    async def close(self) -> None:
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None
