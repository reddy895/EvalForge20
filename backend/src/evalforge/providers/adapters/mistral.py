"""Mistral AI inference provider adapter."""

from src.evalforge.core.config import get_settings
from src.evalforge.providers.openai_compatible import OpenAICompatibleProvider
from src.evalforge.providers.schemas import BenchmarkScoreItem, ModelInfo, ModelPricingItem


def get_mistral_models() -> list[ModelInfo]:
    return [
        ModelInfo(
            id="mistral:mistral-large-latest",
            name="Mistral Large",
            provider="mistral",
            model_identifier="mistral-large-latest",
            family="Mistral",
            parameter_count="123B",
            context_window=128000,
            modalities=["text->text"],
            supports_tools=True,
            supports_structured_output=True,
            license="Mistral Commercial",
            is_commercial_use_allowed=True,
            release_date="2024-07-24",
            description="Mistral's flagship multilingual reasoning and code synthesis model with top reasoning capability.",
            is_local=False,
            is_installed=False,
            is_remote=True,
            benchmarks=[
                BenchmarkScoreItem(benchmark_name="MMLU", metric="accuracy", score=84.0, source="Mistral Technical Announcement", verified=True),
                BenchmarkScoreItem(benchmark_name="HumanEval", metric="pass@1", score=92.0, source="Mistral Technical Announcement", verified=True),
            ],
            pricing=ModelPricingItem(input_cost_per_m=2.00, output_cost_per_m=6.00, currency="USD", is_free_local=False, source_url="https://mistral.ai/technology/#pricing"),
            strengths=["Superior multilingual reasoning (French, German, Spanish, Italian)", "State of the art coding", "128k context"],
            weaknesses=["Cloud API latency higher than local models"],
            recommended_tasks=["multilingual", "coding", "agent", "reasoning"],
        ),
        ModelInfo(
            id="mistral:codestral-latest",
            name="Codestral",
            provider="mistral",
            model_identifier="codestral-latest",
            family="Mistral",
            parameter_count="22B",
            context_window=32768,
            modalities=["text->text"],
            supports_tools=True,
            supports_structured_output=True,
            license="Mistral Non-Production / Commercial Available",
            is_commercial_use_allowed=True,
            release_date="2024-05-29",
            description="Purpose-built coding generation and fill-in-the-middle code completion engine covering 80+ programming languages.",
            is_local=False,
            is_installed=False,
            is_remote=True,
            benchmarks=[
                BenchmarkScoreItem(benchmark_name="HumanEval", metric="pass@1", score=81.1, source="Mistral Codestral Release", verified=True),
            ],
            pricing=ModelPricingItem(input_cost_per_m=0.20, output_cost_per_m=0.60, currency="USD", is_free_local=False, source_url="https://mistral.ai/technology/#pricing"),
            strengths=["Fill-in-the-middle support", "80+ programming languages", "Cost efficient for dev environments"],
            weaknesses=["32k context is shorter than 128k general models"],
            recommended_tasks=["coding", "fill_in_the_middle", "code_review"],
        ),
    ]


class MistralProvider(OpenAICompatibleProvider):
    """Mistral AI inference provider."""

    def __init__(self) -> None:
        settings = get_settings()
        super().__init__(
            name="mistral",
            base_url=settings.MISTRAL_BASE_URL,
            api_key=settings.MISTRAL_API_KEY,
            display_name="Mistral AI",
            provider_type="cloud",
            implementation_status="configurable_cloud",
            setup_instructions="Set MISTRAL_API_KEY in your .env file or environment variables to enable live Mistral evaluations.",
            default_models=get_mistral_models(),
            timeout_seconds=settings.PROVIDER_TIMEOUT_SECONDS,
        )
