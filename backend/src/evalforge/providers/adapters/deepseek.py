"""DeepSeek inference provider adapter."""

from src.evalforge.core.config import get_settings
from src.evalforge.providers.openai_compatible import OpenAICompatibleProvider
from src.evalforge.providers.schemas import BenchmarkScoreItem, ModelInfo, ModelPricingItem


def get_deepseek_models() -> list[ModelInfo]:
    return [
        ModelInfo(
            id="deepseek:deepseek-chat",
            name="DeepSeek V3 (Chat)",
            provider="deepseek",
            model_identifier="deepseek-chat",
            family="DeepSeek",
            parameter_count="671B MoE (37B active)",
            context_window=64000,
            modalities=["text->text"],
            supports_tools=True,
            supports_structured_output=True,
            license="MIT / DeepSeek Open License",
            is_commercial_use_allowed=True,
            release_date="2024-12-26",
            description="Frontier Mixture-of-Experts model trained with Multi-Head Latent Attention matching top closed-source systems at fraction of cost.",
            is_local=False,
            is_installed=False,
            is_remote=True,
            benchmarks=[
                BenchmarkScoreItem(benchmark_name="MMLU", metric="accuracy", score=88.5, source="DeepSeek V3 Technical Report", verified=True),
                BenchmarkScoreItem(benchmark_name="HumanEval", metric="pass@1", score=82.6, source="DeepSeek V3 Technical Report", verified=True),
                BenchmarkScoreItem(benchmark_name="MATH", metric="accuracy", score=75.7, source="DeepSeek V3 Technical Report", verified=True),
            ],
            pricing=ModelPricingItem(input_cost_per_m=0.14, output_cost_per_m=0.28, currency="USD", is_free_local=False, source_url="https://platform.deepseek.com/api-docs/pricing/"),
            strengths=["Unprecedented cost-to-performance ratio", "High coding synthesis", "Native reasoning"],
            weaknesses=["Cloud API availability can face peak load"],
            recommended_tasks=["coding", "reasoning", "math", "general_knowledge"],
        ),
        ModelInfo(
            id="deepseek:deepseek-reasoner",
            name="DeepSeek R1 (Reasoner)",
            provider="deepseek",
            model_identifier="deepseek-reasoner",
            family="DeepSeek",
            parameter_count="671B MoE (37B active)",
            context_window=64000,
            modalities=["text->text"],
            supports_tools=False,
            supports_structured_output=False,
            license="MIT / DeepSeek Open License",
            is_commercial_use_allowed=True,
            release_date="2025-01-20",
            description="Reinforcement-learning-driven reasoning foundation model producing extensive test-time thinking chains.",
            is_local=False,
            is_installed=False,
            is_remote=True,
            benchmarks=[
                BenchmarkScoreItem(benchmark_name="MATH", metric="accuracy", score=97.3, source="DeepSeek R1 Technical Report", verified=True),
                BenchmarkScoreItem(benchmark_name="AIME 2024", metric="pass@1", score=79.8, source="DeepSeek R1 Technical Report", verified=True),
                BenchmarkScoreItem(benchmark_name="Codeforces", metric="percentile", score=96.3, source="DeepSeek R1 Technical Report", verified=True),
            ],
            pricing=ModelPricingItem(input_cost_per_m=0.55, output_cost_per_m=2.19, currency="USD", is_free_local=False, source_url="https://platform.deepseek.com/api-docs/pricing/"),
            strengths=["State of the art mathematical and competition coding reasoning", "Explicit chain of thought introspection"],
            weaknesses=["Higher latency due to chain-of-thought generation tokens"],
            recommended_tasks=["complex_math", "competitive_programming", "formal_logic"],
        ),
    ]


class DeepSeekProvider(OpenAICompatibleProvider):
    """DeepSeek API provider."""

    def __init__(self) -> None:
        settings = get_settings()
        super().__init__(
            name="deepseek",
            base_url=settings.DEEPSEEK_BASE_URL,
            api_key=settings.DEEPSEEK_API_KEY,
            display_name="DeepSeek",
            provider_type="cloud",
            implementation_status="configurable_cloud",
            setup_instructions="Set DEEPSEEK_API_KEY in your .env file or environment variables to enable live DeepSeek inference.",
            default_models=get_deepseek_models(),
            timeout_seconds=settings.PROVIDER_TIMEOUT_SECONDS,
        )
