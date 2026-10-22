"""Google Gemini inference provider adapter."""

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

logger = get_logger("evalforge.providers.gemini")


def get_gemini_models() -> list[ModelInfo]:
    return [
        ModelInfo(
            id="gemini:gemini-1.5-pro",
            name="Google Gemini 1.5 Pro",
            provider="gemini",
            model_identifier="gemini-1.5-pro",
            family="Gemini",
            parameter_count="MoE Multimodal",
            context_window=2000000,
            modalities=["text->text", "image->text", "audio->text", "video->text"],
            supports_tools=True,
            supports_structured_output=True,
            license="Commercial Proprietary",
            is_commercial_use_allowed=True,
            release_date="2024-05-14",
            description="Frontier multimodal model featuring 2-million-token context window with needle recall across hours of audio, video, and codebases.",
            is_local=False,
            is_installed=False,
            is_remote=True,
            benchmarks=[
                BenchmarkScoreItem(benchmark_name="MMLU", metric="accuracy", score=85.9, source="Google Gemini Technical Report", verified=True),
                BenchmarkScoreItem(benchmark_name="HumanEval", metric="pass@1", score=84.1, source="Google Gemini Technical Report", verified=True),
                BenchmarkScoreItem(benchmark_name="MATH", metric="accuracy", score=67.7, source="Google Gemini Technical Report", verified=True),
            ],
            pricing=ModelPricingItem(input_cost_per_m=3.50, output_cost_per_m=10.50, currency="USD", is_free_local=False, source_url="https://ai.google.dev/pricing"),
            strengths=["Record-breaking 2M token context window", "Native audio and video processing", "Deep multimodal reasoning"],
            weaknesses=["Higher latency on massive context prompts"],
            recommended_tasks=["long_context", "multimodal", "code_analysis", "document_qa"],
        ),
        ModelInfo(
            id="gemini:gemini-1.5-flash",
            name="Google Gemini 1.5 Flash",
            provider="gemini",
            model_identifier="gemini-1.5-flash",
            family="Gemini",
            parameter_count="Distilled lightweight",
            context_window=1000000,
            modalities=["text->text", "image->text", "audio->text"],
            supports_tools=True,
            supports_structured_output=True,
            license="Commercial Proprietary",
            is_commercial_use_allowed=True,
            release_date="2024-05-14",
            description="Ultra-fast high-frequency workhorse model with 1M context window and rapid response times.",
            is_local=False,
            is_installed=False,
            is_remote=True,
            benchmarks=[
                BenchmarkScoreItem(benchmark_name="MMLU", metric="accuracy", score=78.9, source="Google Gemini Technical Report", verified=True),
                BenchmarkScoreItem(benchmark_name="HumanEval", metric="pass@1", score=74.3, source="Google Gemini Technical Report", verified=True),
            ],
            pricing=ModelPricingItem(input_cost_per_m=0.075, output_cost_per_m=0.30, currency="USD", is_free_local=False, source_url="https://ai.google.dev/pricing"),
            strengths=["Extremely low per-token cost", "1M context window", "Very fast response generation"],
            weaknesses=["Slightly lower reasoning depth than Pro on complex mathematics"],
            recommended_tasks=["high_volume", "rag", "summarization", "structured_json"],
        ),
    ]


class GeminiProvider(BaseProvider):
    """Google Gemini REST API adapter."""

    def __init__(self) -> None:
        settings = get_settings()
        self.api_key = settings.GEMINI_API_KEY
        self.base_url = settings.GEMINI_BASE_URL.rstrip("/")
        self.timeout_seconds = settings.PROVIDER_TIMEOUT_SECONDS
        super().__init__(
            name="gemini",
            config={"base_url": self.base_url, "has_api_key": bool(self.api_key)},
            display_name="Google Gemini",
            provider_type="cloud",
            implementation_status="configurable_cloud",
            setup_instructions="Set GEMINI_API_KEY in your .env file or environment variables to enable live Google Gemini evaluations.",
        )
        self._client: httpx.AsyncClient | None = None

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key and len(self.api_key.strip()) > 0)

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(self.timeout_seconds, connect=10.0),
                headers={"Content-Type": "application/json"},
            )
        return self._client

    async def health_check(self) -> bool:
        if not self.is_configured:
            return False
        return True

    async def list_models(self) -> list[ModelInfo]:
        return get_gemini_models()

    async def get_model_capabilities(self, model_id: str) -> ProviderCapabilities:
        return ProviderCapabilities(
            supports_chat=True,
            supports_generation=True,
            supports_streaming=True,
            supports_tools=True,
            supports_structured_output=True,
            supports_system_prompt=True,
            max_context_length=2000000,
        )

    async def generate(self, request: InferenceRequest) -> InferenceResponse:
        if not self.is_configured:
            raise ProviderError(
                f"Provider 'gemini' is not configured with an API key. {self.setup_instructions}",
                provider="gemini",
            )

        start_time = time.perf_counter()
        client = await self._get_client()

        target_model = request.model
        if ":" in target_model and target_model.startswith("gemini:"):
            target_model = target_model.split(":", 1)[1]

        # Convert prompt / messages to Gemini contents structure
        contents: list[dict[str, Any]] = []
        if request.messages:
            for m in request.messages:
                role = "user" if m.role == "user" else "model"
                contents.append({"role": role, "parts": [{"text": m.content}]})
        elif request.prompt:
            contents.append({"role": "user", "parts": [{"text": request.prompt}]})

        body: dict[str, Any] = {
            "contents": contents,
            "generationConfig": {
                "temperature": request.temperature,
            },
        }
        if request.system_prompt:
            body["systemInstruction"] = {"parts": [{"text": request.system_prompt}]}
        if request.max_tokens:
            body["generationConfig"]["maxOutputTokens"] = request.max_tokens
        if request.top_p:
            body["generationConfig"]["topP"] = request.top_p

        url = f"{self.base_url}/models/{target_model}:generateContent?key={self.api_key}"
        try:
            resp = await client.post(url, json=body)
            if resp.status_code == 200:
                data = resp.json()
                candidates = data.get("candidates", [])
                response_text = ""
                if candidates:
                    parts = candidates[0].get("content", {}).get("parts", [])
                    response_text = "".join([p.get("text", "") for p in parts])

                usage_meta = data.get("usageMetadata", {})
                usage = TokenUsage(
                    prompt_tokens=usage_meta.get("promptTokenCount"),
                    completion_tokens=usage_meta.get("candidatesTokenCount"),
                    total_tokens=usage_meta.get("totalTokenCount"),
                )

                duration_ms = (time.perf_counter() - start_time) * 1000
                return InferenceResponse(
                    text=response_text,
                    model=request.model,
                    provider="gemini",
                    latency_ms=round(duration_ms, 2),
                    usage=usage,
                    tool_calls=None,
                    raw_metadata={"model": target_model},
                )
            if resp.status_code == 404:
                raise ModelNotFoundError(request.model, "gemini")
            raise ProviderError(f"Gemini API returned HTTP {resp.status_code}: {resp.text[:250]}", provider="gemini")
        except (ModelNotFoundError, ProviderError):
            raise
        except Exception as exc:
            raise ProviderError(f"Gemini error: {exc}", provider="gemini") from exc

    async def close(self) -> None:
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None
