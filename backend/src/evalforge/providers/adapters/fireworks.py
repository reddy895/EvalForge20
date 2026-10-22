"""Fireworks AI inference provider adapter."""

from src.evalforge.core.config import get_settings
from src.evalforge.providers.openai_compatible import OpenAICompatibleProvider
from src.evalforge.providers.schemas import BenchmarkScoreItem, ModelInfo, ModelPricingItem


def get_fireworks_models() -> list[ModelInfo]:
    return [
        ModelInfo(
            id="fireworks:accounts/fireworks/models/llama-v3p1-70b-instruct",
            name="Llama 3.1 70B Instruct (Fireworks)",
            provider="fireworks",
            model_identifier="accounts/fireworks/models/llama-v3p1-70b-instruct",
            family="Llama",
            parameter_count="70.6B",
            context_window=131072,
            modalities=["text->text"],
            supports_tools=True,
            supports_structured_output=True,
            license="Llama 3.1 Community License",
            is_commercial_use_allowed=True,
            release_date="2024-07-23",
            description="Ultra-fast speculative-decoding enabled execution on Fireworks AI infrastructure.",
            is_local=False,
            is_installed=False,
            is_remote=True,
            benchmarks=[
                BenchmarkScoreItem(benchmark_name="MMLU", metric="accuracy", score=83.6, source="Fireworks Technical Evaluation", verified=True),
            ],
            pricing=ModelPricingItem(input_cost_per_m=0.90, output_cost_per_m=0.90, currency="USD", is_free_local=False, source_url="https://fireworks.ai/pricing"),
            strengths=["Low time-to-first-token", "Speculative decoding speedup", "Function calling optimization"],
            weaknesses=["Cloud API dependency"],
            recommended_tasks=["agent", "real_time_interaction", "coding"],
        ),
    ]


class FireworksProvider(OpenAICompatibleProvider):
    """Fireworks AI provider."""

    def __init__(self) -> None:
        settings = get_settings()
        super().__init__(
            name="fireworks",
            base_url=settings.FIREWORKS_BASE_URL,
            api_key=settings.FIREWORKS_API_KEY,
            display_name="Fireworks AI",
            provider_type="cloud",
            implementation_status="configurable_cloud",
            setup_instructions="Set FIREWORKS_API_KEY in your .env file or environment variables to enable live Fireworks AI inference.",
            default_models=get_fireworks_models(),
            timeout_seconds=settings.PROVIDER_TIMEOUT_SECONDS,
        )
