"""Groq LPU inference provider adapter."""

from src.evalforge.core.config import get_settings
from src.evalforge.providers.openai_compatible import OpenAICompatibleProvider
from src.evalforge.providers.schemas import BenchmarkScoreItem, ModelInfo, ModelPricingItem


def get_groq_models() -> list[ModelInfo]:
    return [
        ModelInfo(
            id="groq:llama-3.3-70b-versatile",
            name="Llama 3.3 70B Versatile (Groq)",
            provider="groq",
            model_identifier="llama-3.3-70b-versatile",
            family="Llama",
            parameter_count="70B",
            context_window=128000,
            modalities=["text->text"],
            supports_tools=True,
            supports_structured_output=True,
            license="Llama 3.3 Community License",
            is_commercial_use_allowed=True,
            release_date="2024-12-06",
            description="Meta's top 70B model accelerated on Groq LPUs delivering 250+ tokens per second with full 128k context.",
            is_local=False,
            is_installed=False,
            is_remote=True,
            benchmarks=[
                BenchmarkScoreItem(benchmark_name="MMLU", metric="accuracy", score=86.0, source="Meta Llama 3.3 Evaluation", verified=True),
                BenchmarkScoreItem(benchmark_name="HumanEval", metric="pass@1", score=81.7, source="Meta Llama 3.3 Evaluation", verified=True),
            ],
            measured_latency_ms=12.0,
            measured_throughput_tok_s=280.0,
            pricing=ModelPricingItem(input_cost_per_m=0.59, output_cost_per_m=0.79, currency="USD", is_free_local=False, source_url="https://groq.com/pricing/"),
            strengths=["Unmatched token throughput (250+ tok/s)", "State of the art 70B intelligence", "Full tool support"],
            weaknesses=["Rate limits on free tier accounts"],
            recommended_tasks=["real_time_voice", "agent_loop", "coding", "reasoning"],
        ),
        ModelInfo(
            id="groq:llama-3.1-8b-instant",
            name="Llama 3.1 8B Instant (Groq)",
            provider="groq",
            model_identifier="llama-3.1-8b-instant",
            family="Llama",
            parameter_count="8.03B",
            context_window=128000,
            modalities=["text->text"],
            supports_tools=True,
            supports_structured_output=True,
            license="Llama 3.1 Community License",
            is_commercial_use_allowed=True,
            release_date="2024-07-23",
            description="Sub-100ms latency execution on Groq LPU hardware with 128k context.",
            is_local=False,
            is_installed=False,
            is_remote=True,
            benchmarks=[
                BenchmarkScoreItem(benchmark_name="MMLU", metric="accuracy", score=68.4, source="Meta Llama 3.1 Evaluation", verified=True),
                BenchmarkScoreItem(benchmark_name="HumanEval", metric="pass@1", score=72.6, source="Meta Llama 3.1 Evaluation", verified=True),
            ],
            measured_latency_ms=8.5,
            measured_throughput_tok_s=550.0,
            pricing=ModelPricingItem(input_cost_per_m=0.05, output_cost_per_m=0.08, currency="USD", is_free_local=False, source_url="https://groq.com/pricing/"),
            strengths=["Extreme throughput exceeding 500 tok/s", "Ultra low cost", "128k context"],
            weaknesses=["Lower reasoning depth than 70B variants"],
            recommended_tasks=["streaming", "classification", "high_volume"],
        ),
    ]


class GroqProvider(OpenAICompatibleProvider):
    """Groq LPU hardware acceleration provider."""

    def __init__(self) -> None:
        settings = get_settings()
        super().__init__(
            name="groq",
            base_url=settings.GROQ_BASE_URL,
            api_key=settings.GROQ_API_KEY,
            display_name="Groq LPU",
            provider_type="cloud",
            implementation_status="configurable_cloud",
            setup_instructions="Set GROQ_API_KEY in your .env file or environment variables to enable live high-speed Groq inference.",
            default_models=get_groq_models(),
            timeout_seconds=settings.PROVIDER_TIMEOUT_SECONDS,
        )
