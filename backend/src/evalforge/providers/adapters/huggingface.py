"""Hugging Face Inference API provider adapter."""

import time

import httpx

from src.evalforge.core.config import get_settings
from src.evalforge.core.errors import ProviderError
from src.evalforge.providers.base import BaseProvider
from src.evalforge.providers.schemas import (
    BenchmarkScoreItem,
    InferenceRequest,
    InferenceResponse,
    ModelInfo,
    ModelPricingItem,
    ProviderCapabilities,
)


def get_huggingface_models() -> list[ModelInfo]:
    return [
        ModelInfo(
            id="huggingface:Qwen/Qwen2.5-Coder-32B-Instruct",
            name="Qwen 2.5 Coder 32B Instruct (Hugging Face)",
            provider="huggingface",
            model_identifier="Qwen/Qwen2.5-Coder-32B-Instruct",
            family="Qwen",
            parameter_count="32.5B",
            context_window=32768,
            modalities=["text->text"],
            supports_tools=True,
            supports_structured_output=True,
            license="Apache 2.0",
            is_commercial_use_allowed=True,
            release_date="2024-11-12",
            description="Leading 32B coding foundation model hosted directly on Hugging Face Serverless Inference.",
            is_local=False,
            is_installed=False,
            is_remote=True,
            benchmarks=[
                BenchmarkScoreItem(benchmark_name="HumanEval", metric="pass@1", score=92.7, source="Qwen 2.5 Coder Report", verified=True),
            ],
            pricing=ModelPricingItem(input_cost_per_m=0.0, output_cost_per_m=0.0, currency="USD", is_free_local=False, source_url="https://huggingface.co/pricing"),
            strengths=["Top tier open-weights coding", "Apache 2.0 license", "Direct Hugging Face ecosystem integration"],
            weaknesses=["Serverless cold start delays"],
            recommended_tasks=["coding", "repo_qa", "tool_use"],
        ),
    ]


class HuggingFaceProvider(BaseProvider):
    """Hugging Face serverless inference adapter."""

    def __init__(self) -> None:
        settings = get_settings()
        self.api_key = settings.HUGGINGFACE_API_KEY
        self.base_url = settings.HUGGINGFACE_BASE_URL.rstrip("/")
        super().__init__(
            name="huggingface",
            config={"base_url": self.base_url, "has_api_key": bool(self.api_key)},
            display_name="Hugging Face",
            provider_type="cloud",
            implementation_status="configurable_cloud",
            setup_instructions="Set HUGGINGFACE_API_KEY in your .env file or environment variables to enable live Hugging Face inference.",
        )
        self._client: httpx.AsyncClient | None = None

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key and len(self.api_key.strip()) > 0)

    async def health_check(self) -> bool:
        return self.is_configured

    async def list_models(self) -> list[ModelInfo]:
        return get_huggingface_models()

    async def get_model_capabilities(self, model_id: str) -> ProviderCapabilities:
        return ProviderCapabilities(
            supports_chat=True,
            supports_generation=True,
            supports_streaming=False,
            supports_tools=True,
            supports_structured_output=True,
            supports_system_prompt=True,
            max_context_length=32768,
        )

    async def generate(self, request: InferenceRequest) -> InferenceResponse:
        if not self.is_configured:
            raise ProviderError(
                f"Provider 'huggingface' is not configured with an API key. {self.setup_instructions}",
                provider="huggingface",
            )
        start_time = time.perf_counter()
        headers = {"Authorization": f"Bearer {self.api_key}"}
        target_model = request.model
        if ":" in target_model and target_model.startswith("huggingface:"):
            target_model = target_model.split(":", 1)[1]

        prompt_text = request.prompt or ""
        if request.messages:
            prompt_text = "\n".join([f"{m.role}: {m.content}" for m in request.messages])

        url = f"{self.base_url}/{target_model}"
        async with httpx.AsyncClient(timeout=60.0, headers=headers) as client:
            resp = await client.post(url, json={"inputs": prompt_text, "parameters": {"temperature": request.temperature}})
            if resp.status_code == 200:
                data = resp.json()
                text = ""
                if isinstance(data, list) and len(data) > 0 and "generated_text" in data[0]:
                    text = data[0]["generated_text"]
                elif isinstance(data, dict) and "generated_text" in data:
                    text = data["generated_text"]
                else:
                    text = str(data)

                duration_ms = (time.perf_counter() - start_time) * 1000
                return InferenceResponse(
                    text=text,
                    model=request.model,
                    provider="huggingface",
                    latency_ms=round(duration_ms, 2),
                    usage=None,
                    tool_calls=None,
                )
            raise ProviderError(f"Hugging Face API returned HTTP {resp.status_code}: {resp.text[:250]}", provider="huggingface")
