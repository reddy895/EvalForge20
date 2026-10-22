"""OpenAI inference provider adapter."""

from src.evalforge.core.config import get_settings
from src.evalforge.providers.openai_compatible import OpenAICompatibleProvider
from src.evalforge.providers.schemas import BenchmarkScoreItem, ModelInfo, ModelPricingItem


def get_openai_models() -> list[ModelInfo]:
    return [
        ModelInfo(
            id="openai:gpt-4o",
            name="GPT-4o (Omni)",
            provider="openai",
            model_identifier="gpt-4o",
            family="GPT",
            parameter_count="Omni multimodal",
            context_window=128000,
            modalities=["text->text", "image->text"],
            supports_tools=True,
            supports_structured_output=True,
            license="Commercial Proprietary",
            is_commercial_use_allowed=True,
            release_date="2024-05-13",
            description="Flagship multimodal foundation model with high reasoning, vision, and native tool execution.",
            is_local=False,
            is_installed=False,
            is_remote=True,
            benchmarks=[
                BenchmarkScoreItem(benchmark_name="MMLU", metric="accuracy", score=88.7, source="OpenAI Technical Report", verified=True),
                BenchmarkScoreItem(benchmark_name="HumanEval", metric="pass@1", score=90.2, source="OpenAI Technical Report", verified=True),
                BenchmarkScoreItem(benchmark_name="GSM8K", metric="accuracy", score=95.8, source="OpenAI Technical Report", verified=True),
            ],
            pricing=ModelPricingItem(input_cost_per_m=2.50, output_cost_per_m=10.00, currency="USD", is_free_local=False, source_url="https://openai.com/api/pricing/"),
            strengths=["State of the art multimodal reasoning", "Strict JSON schema enforcement", "Robust function calling"],
            weaknesses=["Cloud API dependency", "Commercial API token costs"],
            recommended_tasks=["reasoning", "coding", "agent", "structured_json"],
        ),
        ModelInfo(
            id="openai:gpt-4o-mini",
            name="GPT-4o mini",
            provider="openai",
            model_identifier="gpt-4o-mini",
            family="GPT",
            parameter_count="Lightweight distilled",
            context_window=128000,
            modalities=["text->text", "image->text"],
            supports_tools=True,
            supports_structured_output=True,
            license="Commercial Proprietary",
            is_commercial_use_allowed=True,
            release_date="2024-07-18",
            description="High-speed, cost-efficient model for lightweight reasoning and structured tasks.",
            is_local=False,
            is_installed=False,
            is_remote=True,
            benchmarks=[
                BenchmarkScoreItem(benchmark_name="MMLU", metric="accuracy", score=82.0, source="OpenAI Technical Report", verified=True),
                BenchmarkScoreItem(benchmark_name="HumanEval", metric="pass@1", score=87.0, source="OpenAI Technical Report", verified=True),
                BenchmarkScoreItem(benchmark_name="GSM8K", metric="accuracy", score=91.3, source="OpenAI Technical Report", verified=True),
            ],
            pricing=ModelPricingItem(input_cost_per_m=0.15, output_cost_per_m=0.60, currency="USD", is_free_local=False, source_url="https://openai.com/api/pricing/"),
            strengths=["Extremely affordable pricing", "Fast token throughput", "128k context"],
            weaknesses=["Less nuanced deep mathematical reasoning than GPT-4o"],
            recommended_tasks=["summarization", "structured_json", "filtering", "lightweight_coding"],
        ),
    ]


class OpenAIProvider(OpenAICompatibleProvider):
    """OpenAI API provider implementation."""

    def __init__(self) -> None:
        settings = get_settings()
        super().__init__(
            name="openai",
            base_url=settings.OPENAI_BASE_URL,
            api_key=settings.OPENAI_API_KEY,
            display_name="OpenAI",
            provider_type="cloud",
            implementation_status="configurable_cloud",
            setup_instructions="Set OPENAI_API_KEY in your .env file or environment variables to enable live OpenAI inference.",
            default_models=get_openai_models(),
            timeout_seconds=settings.PROVIDER_TIMEOUT_SECONDS,
        )
