"""Azure OpenAI inference provider adapter."""

from src.evalforge.core.config import get_settings
from src.evalforge.providers.openai_compatible import OpenAICompatibleProvider
from src.evalforge.providers.schemas import BenchmarkScoreItem, ModelInfo, ModelPricingItem


def get_azure_models() -> list[ModelInfo]:
    return [
        ModelInfo(
            id="azure:gpt-4o",
            name="Azure OpenAI GPT-4o",
            provider="azure",
            model_identifier="gpt-4o",
            family="GPT",
            parameter_count="Omni enterprise",
            context_window=128000,
            modalities=["text->text", "image->text"],
            supports_tools=True,
            supports_structured_output=True,
            license="Microsoft Commercial Agreement",
            is_commercial_use_allowed=True,
            release_date="2024-05-13",
            description="Enterprise SLA-backed Azure-hosted GPT-4o with HIPAA, SOC2, and data residency guarantees.",
            is_local=False,
            is_installed=False,
            is_remote=True,
            benchmarks=[
                BenchmarkScoreItem(benchmark_name="MMLU", metric="accuracy", score=88.7, source="Microsoft Azure Technical Reference", verified=True),
                BenchmarkScoreItem(benchmark_name="HumanEval", metric="pass@1", score=90.2, source="Microsoft Azure Technical Reference", verified=True),
            ],
            pricing=ModelPricingItem(input_cost_per_m=2.50, output_cost_per_m=10.00, currency="USD", is_free_local=False, source_url="https://azure.microsoft.com/en-us/pricing/details/cognitive-services/openai-service/"),
            strengths=["Enterprise security & compliance", "Private VNet peering", "SLA uptime"],
            weaknesses=["Enterprise Azure subscription prerequisite"],
            recommended_tasks=["enterprise_compliance", "coding", "agent"],
        ),
    ]


class AzureOpenAIProvider(OpenAICompatibleProvider):
    """Azure OpenAI service provider."""

    def __init__(self) -> None:
        settings = get_settings()
        endpoint = settings.AZURE_OPENAI_ENDPOINT or "https://your-resource.openai.azure.com"
        super().__init__(
            name="azure",
            base_url=endpoint,
            api_key=settings.AZURE_OPENAI_API_KEY,
            display_name="Azure OpenAI",
            provider_type="cloud",
            implementation_status="configurable_cloud",
            setup_instructions="Set AZURE_OPENAI_API_KEY and AZURE_OPENAI_ENDPOINT in your .env file or environment variables.",
            default_models=get_azure_models(),
            extra_headers={"api-key": settings.AZURE_OPENAI_API_KEY or ""},
            timeout_seconds=settings.PROVIDER_TIMEOUT_SECONDS,
        )
