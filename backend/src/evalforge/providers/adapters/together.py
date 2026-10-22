"""Together AI inference provider adapter."""

from src.evalforge.core.config import get_settings
from src.evalforge.providers.openai_compatible import OpenAICompatibleProvider
from src.evalforge.providers.schemas import BenchmarkScoreItem, ModelInfo, ModelPricingItem


def get_together_models() -> list[ModelInfo]:
    return [
        ModelInfo(
            id="together:meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo",
            name="Llama 3.1 70B Instruct Turbo (Together)",
            provider="together",
            model_identifier="meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo",
            family="Llama",
            parameter_count="70.6B",
            context_window=131072,
            modalities=["text->text"],
            supports_tools=True,
            supports_structured_output=True,
            license="Llama 3.1 Community License",
            is_commercial_use_allowed=True,
            release_date="2024-07-23",
            description="High-throughput Meta 70B execution hosted on Together AI dedicated serverless clusters with 128k context.",
            is_local=False,
            is_installed=False,
            is_remote=True,
            benchmarks=[
                BenchmarkScoreItem(benchmark_name="MMLU", metric="accuracy", score=83.6, source="Together AI Benchmarks", verified=True),
                BenchmarkScoreItem(benchmark_name="HumanEval", metric="pass@1", score=80.5, source="Together AI Benchmarks", verified=True),
            ],
            pricing=ModelPricingItem(input_cost_per_m=0.88, output_cost_per_m=0.88, currency="USD", is_free_local=False, source_url="https://www.together.ai/pricing"),
            strengths=["Predictable symmetric pricing", "128k context", "Reliable serverless scaling"],
            weaknesses=["Network variance during cluster cold starts"],
            recommended_tasks=["coding", "agent", "reasoning"],
        ),
    ]


class TogetherProvider(OpenAICompatibleProvider):
    """Together AI provider."""

    def __init__(self) -> None:
        settings = get_settings()
        super().__init__(
            name="together",
            base_url=settings.TOGETHER_BASE_URL,
            api_key=settings.TOGETHER_API_KEY,
            display_name="Together AI",
            provider_type="cloud",
            implementation_status="configurable_cloud",
            setup_instructions="Set TOGETHER_API_KEY in your .env file or environment variables to enable live Together AI evaluations.",
            default_models=get_together_models(),
            timeout_seconds=settings.PROVIDER_TIMEOUT_SECONDS,
        )
