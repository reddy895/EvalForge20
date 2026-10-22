"""Dynamic model discovery, synchronization, and catalog management service."""

from datetime import UTC, datetime

from src.evalforge.core.logging import get_logger
from src.evalforge.providers.registry import get_provider_registry
from src.evalforge.providers.schemas import (
    BenchmarkScoreItem,
    HardwareRequirements,
    ModelInfo,
    ModelPricingItem,
)

logger = get_logger("evalforge.services.model_service")

# Curated verified technical specifications for models
VERIFIED_CATALOG_MODELS: list[ModelInfo] = [
    # --- QWEN FAMILY ---
    ModelInfo(
        id="qwen-2.5-7b-instruct",
        name="Qwen 2.5 7B Instruct",
        provider="Alibaba / Qwen",
        model_identifier="qwen2.5:7b",
        family="Qwen",
        parameter_count="7.61B",
        quantization="Q4_K_M",
        context_window=131072,
        modalities=["text->text"],
        supports_tools=True,
        supports_structured_output=True,
        license="Apache 2.0",
        is_commercial_use_allowed=True,
        release_date="2024-09-19",
        description="Premier 7B open-weights model with 128k context, leading HumanEval coding benchmarks and reliable agent tool calling.",
        is_local=True,
        is_installed=False,
        benchmarks=[
            BenchmarkScoreItem(benchmark_name="HumanEval", metric="pass@1", score=84.8, source="Official Qwen 2.5 Technical Report (Sept 2024)", verified=True),
            BenchmarkScoreItem(benchmark_name="GSM8K", metric="accuracy", score=83.5, source="Official Qwen 2.5 Technical Report (Sept 2024)", verified=True),
            BenchmarkScoreItem(benchmark_name="MMLU", metric="accuracy", score=74.2, source="Official Qwen 2.5 Technical Report (Sept 2024)", verified=True),
        ],
        measured_latency_ms=24.5,
        measured_throughput_tok_s=38.0,
        pricing=ModelPricingItem(input_cost_per_m=0.0, output_cost_per_m=0.0, is_free_local=True),
        hardware=HardwareRequirements(min_ram_gb=8.0, recommended_ram_gb=16.0, min_vram_gb=6.0, quantization="Q4_K_M", context_length=131072, disk_space_gb=4.8),
        strengths=["Top-tier Python and JavaScript generation", "128k context with high needle recall", "Full Apache 2.0 commercial license"],
        weaknesses=["Requires minimum 8GB RAM for smooth CPU execution", "High context KV cache scales with RAM usage"],
        recommended_tasks=["coding", "structured_json", "agent", "rag"],
        unsuitable_tasks=["embedded_low_ram_microcontrollers"],
    ),
    ModelInfo(
        id="qwen-2.5-3b-instruct",
        name="Qwen 2.5 3B Instruct",
        provider="Alibaba / Qwen",
        model_identifier="qwen2.5:3b",
        family="Qwen",
        parameter_count="3.09B",
        quantization="Q4_K_M",
        context_window=32768,
        modalities=["text->text"],
        supports_tools=True,
        supports_structured_output=True,
        license="Qwen Research License",
        is_commercial_use_allowed=True,
        release_date="2024-09-19",
        description="High-density lightweight model excelling in code synthesis, arithmetic, and strict JSON output on edge devices.",
        is_local=True,
        is_installed=False,
        benchmarks=[
            BenchmarkScoreItem(benchmark_name="HumanEval", metric="pass@1", score=72.6, source="Official Qwen 2.5 Technical Report (Sept 2024)", verified=True),
            BenchmarkScoreItem(benchmark_name="GSM8K", metric="accuracy", score=75.8, source="Official Qwen 2.5 Technical Report (Sept 2024)", verified=True),
            BenchmarkScoreItem(benchmark_name="MMLU", metric="accuracy", score=65.4, source="Official Qwen 2.5 Technical Report (Sept 2024)", verified=True),
        ],
        measured_latency_ms=14.2,
        measured_throughput_tok_s=68.5,
        pricing=ModelPricingItem(input_cost_per_m=0.0, output_cost_per_m=0.0, is_free_local=True),
        hardware=HardwareRequirements(min_ram_gb=4.0, recommended_ram_gb=8.0, min_vram_gb=3.0, quantization="Q4_K_M", context_length=32768, disk_space_gb=2.2),
        strengths=["Runs smoothly on 8GB laptops without dedicated GPU", "Fast time-to-first-token", "High JSON schema accuracy"],
        weaknesses=["Lower long-horizon agent planning than 7B variant"],
        recommended_tasks=["structured_json", "classification", "summarization", "low_latency"],
        unsuitable_tasks=["multi_step_system_architecture"],
    ),
    ModelInfo(
        id="qwen-2.5-14b-instruct",
        name="Qwen 2.5 14B Instruct",
        provider="Alibaba / Qwen",
        model_identifier="qwen2.5:14b",
        family="Qwen",
        parameter_count="14.7B",
        quantization="Q4_K_M",
        context_window=131072,
        modalities=["text->text"],
        supports_tools=True,
        supports_structured_output=True,
        license="Apache 2.0",
        is_commercial_use_allowed=True,
        release_date="2024-09-19",
        description="Exceptional mid-size model punching above its weight in mathematical reasoning and enterprise agent workflows.",
        is_local=True,
        is_installed=False,
        benchmarks=[
            BenchmarkScoreItem(benchmark_name="HumanEval", metric="pass@1", score=87.2, source="Official Qwen 2.5 Technical Report", verified=True),
            BenchmarkScoreItem(benchmark_name="MMLU", metric="accuracy", score=79.8, source="Official Qwen 2.5 Technical Report", verified=True),
            BenchmarkScoreItem(benchmark_name="GSM8K", metric="accuracy", score=88.4, source="Official Qwen 2.5 Technical Report", verified=True),
        ],
        measured_latency_ms=45.0,
        measured_throughput_tok_s=22.0,
        pricing=ModelPricingItem(input_cost_per_m=0.0, output_cost_per_m=0.0, is_free_local=True),
        hardware=HardwareRequirements(min_ram_gb=16.0, recommended_ram_gb=32.0, min_vram_gb=12.0, quantization="Q4_K_M", context_length=131072, disk_space_gb=9.0),
        strengths=["Scores near 70B models on HumanEval", "Full Apache 2.0 license", "Solid tool calling"],
        weaknesses=["Requires minimum 16GB system RAM"],
        recommended_tasks=["coding", "agent", "reasoning"],
    ),

    # --- META LLAMA FAMILY ---
    ModelInfo(
        id="llama-3.1-8b-instruct",
        name="Llama 3.1 8B Instruct",
        provider="Meta",
        model_identifier="llama3.1:8b",
        family="Llama",
        parameter_count="8.03B",
        quantization="Q4_K_M",
        context_window=131072,
        modalities=["text->text"],
        supports_tools=True,
        supports_structured_output=True,
        license="Llama 3.1 Community License",
        is_commercial_use_allowed=True,
        release_date="2024-07-23",
        description="Meta's versatile 8B workhorse model with native 128k context, robust tool calling, and high instruction following.",
        is_local=True,
        is_installed=False,
        benchmarks=[
            BenchmarkScoreItem(benchmark_name="HumanEval", metric="pass@1", score=72.6, source="Meta Llama 3.1 Technical Report (July 2024)", verified=True),
            BenchmarkScoreItem(benchmark_name="GSM8K", metric="accuracy", score=79.6, source="Meta Llama 3.1 Technical Report (July 2024)", verified=True),
            BenchmarkScoreItem(benchmark_name="MMLU", metric="accuracy", score=68.4, source="Meta Llama 3.1 Technical Report (July 2024)", verified=True),
        ],
        measured_latency_ms=22.1,
        measured_throughput_tok_s=42.0,
        pricing=ModelPricingItem(input_cost_per_m=0.0, output_cost_per_m=0.0, is_free_local=True),
        hardware=HardwareRequirements(min_ram_gb=8.0, recommended_ram_gb=16.0, min_vram_gb=6.0, quantization="Q4_K_M", context_length=131072, disk_space_gb=4.7),
        strengths=["Broad ecosystem support and Ollama optimization", "128k context length with high retrieval", "Strong instruction adherence"],
        weaknesses=["Slightly lower coding benchmarks compared to Qwen 2.5 7B", "Prompt template requires precise formatting"],
        recommended_tasks=["agent", "rag", "general_reasoning", "conversation"],
    ),
    ModelInfo(
        id="llama-3.2-3b-instruct",
        name="Llama 3.2 3B Instruct",
        provider="Meta",
        model_identifier="llama3.2:3b",
        family="Llama",
        parameter_count="3.21B",
        quantization="Q4_K_M",
        context_window=131072,
        modalities=["text->text"],
        supports_tools=True,
        supports_structured_output=True,
        license="Llama 3.2 Community License",
        is_commercial_use_allowed=True,
        release_date="2024-09-25",
        description="Edge-optimized compact model with 128k context and efficient on-device multilingual comprehension.",
        is_local=True,
        is_installed=False,
        benchmarks=[
            BenchmarkScoreItem(benchmark_name="HumanEval", metric="pass@1", score=65.2, source="Meta Llama 3.2 Technical Announcement (Sept 2024)", verified=True),
            BenchmarkScoreItem(benchmark_name="MMLU", metric="accuracy", score=63.4, source="Meta Llama 3.2 Technical Announcement (Sept 2024)", verified=True),
        ],
        measured_latency_ms=11.8,
        measured_throughput_tok_s=75.0,
        pricing=ModelPricingItem(input_cost_per_m=0.0, output_cost_per_m=0.0, is_free_local=True),
        hardware=HardwareRequirements(min_ram_gb=4.0, recommended_ram_gb=8.0, min_vram_gb=3.0, quantization="Q4_K_M", context_length=131072, disk_space_gb=2.0),
        strengths=["Exceptional throughput on CPU / integrated graphics", "128k context on mobile and edge devices"],
        weaknesses=["Reduced performance on complex multi-step logical deduction"],
        recommended_tasks=["on_device_assistant", "summarization", "lightweight_rag"],
    ),
    ModelInfo(
        id="llama-3.3-70b-instruct",
        name="Llama 3.3 70B Instruct",
        provider="Meta",
        model_identifier="llama3.3:70b",
        family="Llama",
        parameter_count="70.6B",
        quantization="Q4_K_M",
        context_window=131072,
        modalities=["text->text"],
        supports_tools=True,
        supports_structured_output=True,
        license="Llama 3.3 Community License",
        is_commercial_use_allowed=True,
        release_date="2024-12-06",
        description="State of the art open-weights 70B model matching previous 405B capabilities at a fraction of compute.",
        is_local=True,
        is_installed=False,
        benchmarks=[
            BenchmarkScoreItem(benchmark_name="MMLU", metric="accuracy", score=86.0, source="Meta Llama 3.3 Technical Report", verified=True),
            BenchmarkScoreItem(benchmark_name="HumanEval", metric="pass@1", score=81.7, source="Meta Llama 3.3 Technical Report", verified=True),
            BenchmarkScoreItem(benchmark_name="GSM8K", metric="accuracy", score=93.0, source="Meta Llama 3.3 Technical Report", verified=True),
        ],
        pricing=ModelPricingItem(input_cost_per_m=0.0, output_cost_per_m=0.0, is_free_local=True),
        hardware=HardwareRequirements(min_ram_gb=48.0, recommended_ram_gb=64.0, min_vram_gb=40.0, quantization="Q4_K_M", context_length=131072, disk_space_gb=42.0),
        strengths=["Top tier open reasoning", "128k context", "Matches previous 405B benchmarks"],
        weaknesses=["Requires heavy workstation hardware or multi-GPU setup for local execution"],
        recommended_tasks=["complex_reasoning", "coding", "agent"],
    ),

    # --- DEEPSEEK FAMILY ---
    ModelInfo(
        id="deepseek-v3",
        name="DeepSeek V3",
        provider="DeepSeek",
        model_identifier="deepseek-chat",
        family="DeepSeek",
        parameter_count="671B MoE (37B active)",
        context_window=64000,
        modalities=["text->text"],
        supports_tools=True,
        supports_structured_output=True,
        license="DeepSeek Open License",
        is_commercial_use_allowed=True,
        release_date="2024-12-26",
        description="Frontier Mixture-of-Experts architecture delivering top performance at unprecedented inference economics.",
        is_local=False,
        is_installed=False,
        is_remote=True,
        benchmarks=[
            BenchmarkScoreItem(benchmark_name="MMLU", metric="accuracy", score=88.5, source="DeepSeek V3 Tech Report", verified=True),
            BenchmarkScoreItem(benchmark_name="HumanEval", metric="pass@1", score=82.6, source="DeepSeek V3 Tech Report", verified=True),
            BenchmarkScoreItem(benchmark_name="MATH", metric="accuracy", score=75.7, source="DeepSeek V3 Tech Report", verified=True),
        ],
        pricing=ModelPricingItem(input_cost_per_m=0.14, output_cost_per_m=0.28, currency="USD", is_free_local=False, source_url="https://platform.deepseek.com/api-docs/pricing/"),
        strengths=["Cost efficiency", "High code generation", "Multi-Head Latent Attention architecture"],
        weaknesses=["Cloud API dependency for full MoE weights"],
        recommended_tasks=["coding", "reasoning", "math"],
    ),
    ModelInfo(
        id="deepseek-r1",
        name="DeepSeek R1",
        provider="DeepSeek",
        model_identifier="deepseek-reasoner",
        family="DeepSeek",
        parameter_count="671B MoE (37B active)",
        context_window=64000,
        modalities=["text->text"],
        supports_tools=False,
        supports_structured_output=False,
        license="MIT License",
        is_commercial_use_allowed=True,
        release_date="2025-01-20",
        description="Leading open-weights reasoning model with explicit test-time thinking chains rivaling closed reasoning systems.",
        is_local=False,
        is_installed=False,
        is_remote=True,
        benchmarks=[
            BenchmarkScoreItem(benchmark_name="MATH", metric="accuracy", score=97.3, source="DeepSeek R1 Tech Report", verified=True),
            BenchmarkScoreItem(benchmark_name="AIME 2024", metric="pass@1", score=79.8, source="DeepSeek R1 Tech Report", verified=True),
        ],
        pricing=ModelPricingItem(input_cost_per_m=0.55, output_cost_per_m=2.19, currency="USD", is_free_local=False, source_url="https://platform.deepseek.com/api-docs/pricing/"),
        strengths=["State of the art mathematical deduction", "Chain of thought introspection"],
        weaknesses=["Slower latency due to chain-of-thought token generation"],
        recommended_tasks=["complex_math", "competitive_programming", "formal_logic"],
    ),

    # --- MISTRAL FAMILY ---
    ModelInfo(
        id="mistral-nemo-12b-instruct",
        name="Mistral NeMo 12B Instruct",
        provider="Mistral AI / NVIDIA",
        model_identifier="mistral-nemo:12b",
        family="Mistral",
        parameter_count="12.2B",
        quantization="Q4_K_M",
        context_window=131072,
        modalities=["text->text"],
        supports_tools=True,
        supports_structured_output=True,
        license="Apache 2.0",
        is_commercial_use_allowed=True,
        release_date="2024-07-18",
        description="Joint Mistral-NVIDIA 12B model featuring the Tekken tokenizer with 128k context and multilingual coding strengths.",
        is_local=True,
        is_installed=False,
        benchmarks=[
            BenchmarkScoreItem(benchmark_name="HumanEval", metric="pass@1", score=70.1, source="Mistral NeMo Technical Announcement (July 2024)", verified=True),
            BenchmarkScoreItem(benchmark_name="MMLU", metric="accuracy", score=68.0, source="Mistral NeMo Technical Announcement (July 2024)", verified=True),
        ],
        measured_latency_ms=36.0,
        measured_throughput_tok_s=27.5,
        pricing=ModelPricingItem(input_cost_per_m=0.0, output_cost_per_m=0.0, is_free_local=True),
        hardware=HardwareRequirements(min_ram_gb=12.0, recommended_ram_gb=24.0, min_vram_gb=10.0, quantization="Q4_K_M", context_length=131072, disk_space_gb=7.5),
        strengths=["Tekken tokenizer handles multi-language code efficiently", "Apache 2.0 license", "128k context"],
        weaknesses=["Higher RAM requirement than 8B models"],
        recommended_tasks=["multilingual_coding", "rag", "summarization"],
    ),

    # --- CLOUD FRONTIER MODELS ---
    ModelInfo(
        id="claude-3-5-sonnet",
        name="Claude 3.5 Sonnet",
        provider="Anthropic",
        model_identifier="claude-3-5-sonnet-20241022",
        family="Claude",
        parameter_count="Frontier",
        context_window=200000,
        modalities=["text->text", "image->text"],
        supports_tools=True,
        supports_structured_output=True,
        license="Commercial Proprietary",
        is_commercial_use_allowed=True,
        release_date="2024-10-22",
        description="Top benchmark-ranking frontier foundation model excelling across coding, multi-turn reasoning, and complex tool calling.",
        is_local=False,
        is_installed=False,
        is_remote=True,
        benchmarks=[
            BenchmarkScoreItem(benchmark_name="HumanEval", metric="pass@1", score=93.7, source="Anthropic Claude 3.5 Sonnet Card", verified=True),
            BenchmarkScoreItem(benchmark_name="MMLU", metric="accuracy", score=88.7, source="Anthropic Claude 3.5 Sonnet Card", verified=True),
            BenchmarkScoreItem(benchmark_name="GSM8K", metric="accuracy", score=96.4, source="Anthropic Claude 3.5 Sonnet Card", verified=True),
        ],
        pricing=ModelPricingItem(input_cost_per_m=3.00, output_cost_per_m=15.00, currency="USD", is_free_local=False, source_url="https://anthropic.com/pricing"),
        strengths=["Frontier coding benchmarks", "200k context window", "Reliable agent loops"],
        weaknesses=["Requires cloud API connectivity and API credits"],
        recommended_tasks=["coding", "agent", "reasoning", "complex_analysis"],
    ),
    ModelInfo(
        id="gpt-4o",
        name="GPT-4o (Omni)",
        provider="OpenAI",
        model_identifier="gpt-4o",
        family="GPT",
        parameter_count="Omni Multimodal",
        context_window=128000,
        modalities=["text->text", "image->text"],
        supports_tools=True,
        supports_structured_output=True,
        license="Commercial Proprietary",
        is_commercial_use_allowed=True,
        release_date="2024-05-13",
        description="OpenAI's flagship multimodal intelligence with high reasoning, vision, and native tool execution.",
        is_local=False,
        is_installed=False,
        is_remote=True,
        benchmarks=[
            BenchmarkScoreItem(benchmark_name="MMLU", metric="accuracy", score=88.7, source="OpenAI Technical Report", verified=True),
            BenchmarkScoreItem(benchmark_name="HumanEval", metric="pass@1", score=90.2, source="OpenAI Technical Report", verified=True),
            BenchmarkScoreItem(benchmark_name="GSM8K", metric="accuracy", score=95.8, source="OpenAI Technical Report", verified=True),
        ],
        pricing=ModelPricingItem(input_cost_per_m=2.50, output_cost_per_m=10.00, currency="USD", is_free_local=False, source_url="https://openai.com/api/pricing/"),
        strengths=["High multimodal reasoning", "Strict JSON schema enforcement", "Universal tool calling"],
        weaknesses=["Proprietary closed cloud service"],
        recommended_tasks=["reasoning", "coding", "agent", "structured_json"],
    ),
    ModelInfo(
        id="gemini-1.5-pro",
        name="Gemini 1.5 Pro",
        provider="Google",
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
        description="Unprecedented 2-million-token context window with high needle-in-a-haystack recall across text, audio, and video.",
        is_local=False,
        is_installed=False,
        is_remote=True,
        benchmarks=[
            BenchmarkScoreItem(benchmark_name="MMLU", metric="accuracy", score=85.9, source="Google Gemini Tech Report", verified=True),
            BenchmarkScoreItem(benchmark_name="HumanEval", metric="pass@1", score=84.1, source="Google Gemini Tech Report", verified=True),
            BenchmarkScoreItem(benchmark_name="MATH", metric="accuracy", score=67.7, source="Google Gemini Tech Report", verified=True),
        ],
        pricing=ModelPricingItem(input_cost_per_m=3.50, output_cost_per_m=10.50, currency="USD", is_free_local=False, source_url="https://ai.google.dev/pricing"),
        strengths=["2M token context window", "Native audio and video multimodal processing"],
        weaknesses=["Latency increases with context size"],
        recommended_tasks=["long_context", "multimodal", "code_analysis", "document_qa"],
    ),

    # --- DETERMINISTIC TEST MOCKS ---
    ModelInfo(
        id="mock-llama-3.1-8b",
        name="Mock Llama 3.1 8B Instruct",
        provider="mock",
        model_identifier="mock-llama-3.1-8b",
        family="llama",
        parameter_count="8B",
        quantization="Q4_K_M",
        context_window=8192,
        modalities=["text->text"],
        supports_tools=True,
        supports_structured_output=True,
        license="MIT",
        is_commercial_use_allowed=True,
        description="Hermetic mock model for deterministic local offline testing with zero external API calls.",
        is_local=True,
        is_installed=True,
        benchmarks=[
            BenchmarkScoreItem(benchmark_name="Synthetic", metric="score", score=99.0, source="Deterministic Test Suite", verified=True),
        ],
        pricing=ModelPricingItem(input_cost_per_m=0.0, output_cost_per_m=0.0, is_free_local=True),
        strengths=["Zero latency and deterministic outputs", "No internet connection or daemon required"],
        weaknesses=["Synthetic canned outputs only"],
        recommended_tasks=["testing", "ci_cd", "dry_run"],
    ),
    ModelInfo(
        id="mock-qwen-2.5-7b",
        name="Mock Qwen 2.5 7B Instruct",
        provider="mock",
        model_identifier="mock-qwen-2.5-7b",
        family="qwen2",
        parameter_count="7B",
        quantization="Q4_K_M",
        context_window=8192,
        modalities=["text->text"],
        supports_tools=True,
        supports_structured_output=True,
        license="MIT",
        is_commercial_use_allowed=True,
        description="Hermetic mock model simulating Qwen structured output responses.",
        is_local=True,
        is_installed=True,
        pricing=ModelPricingItem(input_cost_per_m=0.0, output_cost_per_m=0.0, is_free_local=True),
        strengths=["Zero latency deterministic output"],
        weaknesses=["Synthetic canned outputs only"],
        recommended_tasks=["testing", "ci_cd"],
    ),
]


class ModelService:
    """Manages dynamic model discovery, Ollama sync, and verified catalog queries."""

    _cached_models: list[ModelInfo] | None = None
    _last_synced: str | None = None

    @classmethod
    async def get_all_models(cls, force_refresh: bool = False) -> list[ModelInfo]:
        """Fetch models from registry and dynamic discovery, merging with verified catalog."""
        if cls._cached_models is not None and not force_refresh:
            return list(cls._cached_models)

        registry = get_provider_registry()
        models_by_id: dict[str, ModelInfo] = {}

        # 1. Seed with curated verified catalog models
        for m in VERIFIED_CATALOG_MODELS:
            models_by_id[m.id] = m.model_copy(deep=True)

        # 2. Check local Ollama daemon for dynamically installed models
        try:
            ollama = registry.get("ollama")
            ollama_models = await ollama.list_models()
            for om in ollama_models:
                # Check if this matches a known model
                matched = False
                for cat_model in models_by_id.values():
                    if (
                        cat_model.model_identifier
                        and om.id.startswith(cat_model.model_identifier)
                        or (om.name and cat_model.model_identifier and cat_model.model_identifier in om.name)
                    ):
                        cat_model.is_installed = True
                        cat_model.is_local = True
                        cat_model.size_bytes = om.size_bytes
                        cat_model.quantization = om.quantization or cat_model.quantization
                        cat_model.parameter_count = om.parameter_size or cat_model.parameter_count
                        matched = True
                        break

                if not matched:
                    # Add newly discovered model from local Ollama
                    models_by_id[f"ollama:{om.id}"] = ModelInfo(
                        id=f"ollama:{om.id}",
                        name=om.name or om.id,
                        provider="Ollama (Local)",
                        model_identifier=om.id,
                        size_bytes=om.size_bytes,
                        parameter_count=om.parameter_size,
                        quantization=om.quantization,
                        family=om.family or "unknown",
                        is_local=True,
                        is_installed=True,
                        description=f"Discovered dynamically from local Ollama instance ({om.id}).",
                        hardware=HardwareRequirements(
                            min_ram_gb=8.0,
                            recommended_ram_gb=16.0,
                            quantization=om.quantization or "Q4_K_M",
                            context_length=8192,
                            disk_space_gb=round((om.size_bytes or 4000000000) / 1e9, 1),
                        ),
                    )
        except Exception as exc:
            logger.debug("Ollama model discovery skipped: %s", exc)

        # 3. Discover from configured cloud providers
        cloud_providers = ["openai", "groq", "mistral", "deepseek", "together", "fireworks"]
        for p_name in cloud_providers:
            try:
                p = registry.get(p_name)
                if getattr(p, "is_configured", False):
                    cloud_models = await p.list_models()
                    for cm in cloud_models:
                        if cm.id not in models_by_id:
                            models_by_id[cm.id] = cm
            except Exception as exc:
                logger.debug("Cloud discovery error for %s: %s", p_name, exc)

        cls._cached_models = list(models_by_id.values())
        cls._last_synced = datetime.now(UTC).isoformat()
        return list(cls._cached_models)

    @classmethod
    async def filter_models(
        cls,
        query: str | None = None,
        provider: str | None = None,
        task: str | None = None,
        is_local: bool | None = None,
        is_installed: bool | None = None,
        supports_tools: bool | None = None,
        supports_structured_output: bool | None = None,
        sort_by: str = "recommended",
        offset: int = 0,
        limit: int = 50,
        force_refresh: bool = False,
    ) -> tuple[list[ModelInfo], int]:
        """Search, filter, sort, and paginate model catalog."""
        all_models = await cls.get_all_models(force_refresh=force_refresh)
        results = all_models

        # Text search
        if query and query.strip():
            q = query.strip().lower()
            results = [
                m
                for m in results
                if q in m.name.lower()
                or q in m.provider.lower()
                or (m.family and q in m.family.lower())
                or (m.description and q in m.description.lower())
                or (m.model_identifier and q in m.model_identifier.lower())
            ]

        # Provider filter
        if provider and provider != "all":
            p = provider.lower()
            results = [m for m in results if p in m.provider.lower() or p in m.id.lower()]

        # Task filter
        if task and task != "all":
            t = task.lower()
            results = [m for m in results if any(t in task_tag.lower() for task_tag in m.recommended_tasks)]

        # Local / Cloud
        if is_local is not None:
            results = [m for m in results if m.is_local == is_local]

        # Installed
        if is_installed is not None:
            results = [m for m in results if m.is_installed == is_installed]

        # Capabilities
        if supports_tools is not None:
            results = [m for m in results if m.supports_tools == supports_tools]

        if supports_structured_output is not None:
            results = [m for m in results if m.supports_structured_output == supports_structured_output]

        # Sorting
        if sort_by == "benchmark":
            results.sort(key=lambda m: m.benchmarks[0].score if m.benchmarks else 0, reverse=True)
        elif sort_by == "context":
            results.sort(key=lambda m: m.context_window, reverse=True)
        elif sort_by == "ram":
            results.sort(key=lambda m: m.hardware.min_ram_gb)
        elif sort_by == "name":
            results.sort(key=lambda m: m.name.lower())

        total = len(results)
        paged = results[offset : offset + limit]
        return paged, total


_model_service: ModelService | None = None


def get_model_service() -> ModelService:
    """Return or initialize the singleton ModelService instance."""
    global _model_service
    if _model_service is None:
        _model_service = ModelService()
    return _model_service

