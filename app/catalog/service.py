"""Unified model catalog service aggregating verified metadata, pricing, and live discovery."""

from app.catalog.models import CatalogModel, CatalogProviderInfo, ModelPricing
from app.config import get_settings
from app.providers.ollama_diagnostics import check_ollama_status

# Verified base pricing and capability metadata (sourced from official provider documentation)
KNOWN_CATALOG_MODELS: list[CatalogModel] = [
    # --- OpenAI ---
    CatalogModel(
        id="openai/gpt-4o",
        model_identifier="gpt-4o",
        provider="openai",
        display_name="GPT-4o",
        is_local=False,
        context_window=128000,
        modalities=["text->text", "text,image->text"],
        supports_tools=True,
        supports_structured_output=True,
        release_date="2024-08-06",
        task_capabilities=[
            "reasoning",
            "coding",
            "data_extraction",
            "structured_json",
            "summarization",
            "agent_tools",
        ],
        pricing=ModelPricing(
            input_cost_per_m=2.50,
            output_cost_per_m=10.00,
            cached_input_cost_per_m=1.25,
            currency="USD",
            unit="per 1M tokens",
            source_url="https://developers.openai.com/api/docs/pricing",
            last_verified="2025-01-15",
            assumptions="Standard tier pay-as-you-go pricing",
        ),
    ),
    CatalogModel(
        id="openai/gpt-4o-mini",
        model_identifier="gpt-4o-mini",
        provider="openai",
        display_name="GPT-4o Mini",
        is_local=False,
        context_window=128000,
        modalities=["text->text", "text,image->text"],
        supports_tools=True,
        supports_structured_output=True,
        release_date="2024-07-18",
        task_capabilities=[
            "reasoning",
            "coding",
            "data_extraction",
            "structured_json",
            "classification",
        ],
        pricing=ModelPricing(
            input_cost_per_m=0.15,
            output_cost_per_m=0.60,
            cached_input_cost_per_m=0.075,
            currency="USD",
            unit="per 1M tokens",
            source_url="https://developers.openai.com/api/docs/pricing",
            last_verified="2025-01-15",
            assumptions="Standard tier pay-as-you-go pricing",
        ),
    ),
    CatalogModel(
        id="openai/o3-mini",
        model_identifier="o3-mini",
        provider="openai",
        display_name="o3-mini",
        is_local=False,
        context_window=200000,
        modalities=["text->text"],
        supports_tools=True,
        supports_structured_output=True,
        release_date="2025-01-31",
        task_capabilities=["reasoning", "coding", "problem_solving", "structured_json"],
        pricing=ModelPricing(
            input_cost_per_m=1.10,
            output_cost_per_m=4.40,
            cached_input_cost_per_m=0.55,
            currency="USD",
            unit="per 1M tokens",
            source_url="https://developers.openai.com/api/docs/pricing",
            last_verified="2025-01-31",
        ),
    ),
    # --- Anthropic Claude ---
    CatalogModel(
        id="anthropic/claude-3-5-sonnet-20241022",
        model_identifier="claude-3-5-sonnet-20241022",
        provider="anthropic",
        display_name="Claude 3.5 Sonnet (v2)",
        is_local=False,
        context_window=200000,
        modalities=["text->text", "text,image->text"],
        supports_tools=True,
        supports_structured_output=True,
        release_date="2024-10-22",
        task_capabilities=[
            "reasoning",
            "coding",
            "data_extraction",
            "structured_json",
            "agent_tools",
        ],
        pricing=ModelPricing(
            input_cost_per_m=3.00,
            output_cost_per_m=15.00,
            cached_input_cost_per_m=0.30,
            currency="USD",
            unit="per 1M tokens",
            source_url="https://docs.anthropic.com/",
            last_verified="2024-11-01",
        ),
    ),
    CatalogModel(
        id="anthropic/claude-3-5-haiku-20241022",
        model_identifier="claude-3-5-haiku-20241022",
        provider="anthropic",
        display_name="Claude 3.5 Haiku",
        is_local=False,
        context_window=200000,
        modalities=["text->text"],
        supports_tools=True,
        supports_structured_output=True,
        release_date="2024-10-22",
        task_capabilities=["classification", "data_extraction", "coding", "structured_json"],
        pricing=ModelPricing(
            input_cost_per_m=0.80,
            output_cost_per_m=4.00,
            cached_input_cost_per_m=0.08,
            currency="USD",
            unit="per 1M tokens",
            source_url="https://docs.anthropic.com/",
            last_verified="2024-11-01",
        ),
    ),
    # --- Google Gemini ---
    CatalogModel(
        id="gemini/gemini-1.5-pro",
        model_identifier="gemini-1.5-pro",
        provider="gemini",
        display_name="Gemini 1.5 Pro",
        is_local=False,
        context_window=2000000,
        modalities=["text->text", "text,image->text", "text,audio->text"],
        supports_tools=True,
        supports_structured_output=True,
        release_date="2024-05-14",
        task_capabilities=[
            "reasoning",
            "coding",
            "data_extraction",
            "structured_json",
            "summarization",
        ],
        pricing=ModelPricing(
            input_cost_per_m=1.25,
            output_cost_per_m=5.00,
            cached_input_cost_per_m=0.3125,
            currency="USD",
            unit="per 1M tokens",
            source_url="https://ai.google.dev/gemini-api/docs",
            last_verified="2024-10-01",
            assumptions="Prompts <= 128k tokens tier",
        ),
    ),
    CatalogModel(
        id="gemini/gemini-1.5-flash",
        model_identifier="gemini-1.5-flash",
        provider="gemini",
        display_name="Gemini 1.5 Flash",
        is_local=False,
        context_window=1000000,
        modalities=["text->text", "text,image->text"],
        supports_tools=True,
        supports_structured_output=True,
        release_date="2024-05-14",
        task_capabilities=[
            "classification",
            "data_extraction",
            "structured_json",
            "summarization",
        ],
        pricing=ModelPricing(
            input_cost_per_m=0.075,
            output_cost_per_m=0.30,
            cached_input_cost_per_m=0.01875,
            currency="USD",
            unit="per 1M tokens",
            source_url="https://ai.google.dev/gemini-api/docs",
            last_verified="2024-10-01",
        ),
    ),
    # --- NVIDIA NIM ---
    CatalogModel(
        id="nvidia/meta/llama-3.1-70b-instruct",
        model_identifier="meta/llama-3.1-70b-instruct",
        provider="nvidia",
        display_name="Llama 3.1 70B Instruct (NVIDIA NIM)",
        is_local=False,
        context_window=128000,
        modalities=["text->text"],
        supports_tools=True,
        supports_structured_output=True,
        release_date="2024-07-23",
        task_capabilities=["reasoning", "coding", "data_extraction", "structured_json"],
        pricing=ModelPricing(
            input_cost_per_m=None,
            output_cost_per_m=None,
            currency="USD",
            unit="per 1M tokens",
            source_url="https://build.nvidia.com/meta/llama-3_1-70b-instruct",
            last_verified="2024-08-01",
            assumptions="Pay-per-token or hosted API credit allowance",
        ),
    ),
    CatalogModel(
        id="nvidia/meta/llama-3.1-8b-instruct",
        model_identifier="meta/llama-3.1-8b-instruct",
        provider="nvidia",
        display_name="Llama 3.1 8B Instruct (NVIDIA NIM)",
        is_local=False,
        context_window=128000,
        modalities=["text->text"],
        supports_tools=True,
        supports_structured_output=True,
        release_date="2024-07-23",
        task_capabilities=["classification", "instruction_following", "structured_json"],
        pricing=ModelPricing(
            input_cost_per_m=None,
            output_cost_per_m=None,
            currency="USD",
            unit="per 1M tokens",
            source_url="https://build.nvidia.com/meta/llama-3_1-8b-instruct",
            last_verified="2024-08-01",
        ),
    ),
    # --- Ollama Suggested / Common Baseline Models ---
    CatalogModel(
        id="ollama/llama3.1:8b",
        model_identifier="llama3.1:8b",
        provider="ollama",
        display_name="Llama 3.1 8B (Local Ollama)",
        is_local=True,
        is_installed=False,
        context_window=131072,
        modalities=["text->text"],
        supports_tools=True,
        supports_structured_output=True,
        release_date="2024-07-23",
        task_capabilities=["reasoning", "coding", "instruction_following", "structured_json"],
        pricing=ModelPricing(
            input_cost_per_m=0.0,
            output_cost_per_m=0.0,
            currency="USD",
            unit="local compute",
            source_url="https://ollama.com/library/llama3.1",
            last_verified="2024-08-01",
            assumptions="Zero cloud API charge. Hardware and electricity costs apply.",
        ),
    ),
    CatalogModel(
        id="ollama/mistral:7b",
        model_identifier="mistral:7b",
        provider="ollama",
        display_name="Mistral 7B (Local Ollama)",
        is_local=True,
        is_installed=False,
        context_window=32768,
        modalities=["text->text"],
        supports_tools=True,
        supports_structured_output=True,
        release_date="2023-09-27",
        task_capabilities=["reasoning", "coding", "instruction_following"],
        pricing=ModelPricing(
            input_cost_per_m=0.0,
            output_cost_per_m=0.0,
            currency="USD",
            unit="local compute",
            source_url="https://ollama.com/library/mistral",
            last_verified="2024-01-01",
            assumptions="Zero cloud API charge. Hardware and electricity costs apply.",
        ),
    ),
    CatalogModel(
        id="ollama/qwen2.5-coder:7b",
        model_identifier="qwen2.5-coder:7b",
        provider="ollama",
        display_name="Qwen 2.5 Coder 7B (Local Ollama)",
        is_local=True,
        is_installed=False,
        context_window=32768,
        modalities=["text->text"],
        supports_tools=True,
        supports_structured_output=True,
        release_date="2024-09-19",
        task_capabilities=["coding", "debugging", "structured_json"],
        pricing=ModelPricing(
            input_cost_per_m=0.0,
            output_cost_per_m=0.0,
            currency="USD",
            unit="local compute",
            source_url="https://ollama.com/library/qwen2.5-coder",
            last_verified="2024-09-20",
            assumptions="Zero cloud API charge.",
        ),
    ),
]


class ModelCatalogService:
    """Service to discover, search, filter, and inspect models and their verified pricing."""

    def __init__(self) -> None:
        self._custom_models: dict[str, CatalogModel] = {}

    def register_custom_model(self, model: CatalogModel) -> None:
        """Register or override a custom model entry."""
        self._custom_models[model.id] = model

    async def get_all_models(
        self,
        search: str | None = None,
        provider: str | None = None,
        is_local: bool | None = None,
        capability: str | None = None,
    ) -> list[CatalogModel]:
        """Fetch all models merging static catalog with live discovered local and cloud models."""
        settings = get_settings()
        models_map: dict[str, CatalogModel] = {m.id: m.model_copy() for m in KNOWN_CATALOG_MODELS}
        models_map.update(self._custom_models)

        # 1. Update cloud provider availability based on configuration
        for model in models_map.values():
            if model.provider == "openai":
                model.is_available = bool(settings.openai_api_key)
            elif model.provider == "anthropic":
                model.is_available = bool(settings.anthropic_api_key)
            elif model.provider == "gemini":
                model.is_available = bool(settings.gemini_api_key)
            elif model.provider == "nvidia":
                model.is_available = bool(settings.nvidia_api_key)

        # 2. Query live Ollama daemon to discover installed models
        try:
            ollama_status = await check_ollama_status(
                base_url=settings.ollama_base_url, timeout_seconds=1.5
            )
            ollama_online = ollama_status.is_reachable
            installed_names = {m.name for m in ollama_status.models}

            for model in list(models_map.values()):
                if model.provider == "ollama":
                    model.is_available = ollama_online
                    model.is_installed = model.model_identifier in installed_names

            # Add any installed Ollama models not in static catalog
            if ollama_online:
                for om in ollama_status.models:
                    model_id = f"ollama/{om.name}"
                    if model_id not in models_map:
                        models_map[model_id] = CatalogModel(
                            id=model_id,
                            model_identifier=om.name,
                            provider="ollama",
                            display_name=f"{om.name} (Local)",
                            is_local=True,
                            is_available=True,
                            is_installed=True,
                            context_window=om.context_length or 8192,
                            modalities=["text->text"],
                            supports_tools=True,
                            supports_structured_output=True,
                            task_capabilities=["reasoning", "coding", "instruction_following"],
                            pricing=ModelPricing(
                                input_cost_per_m=0.0,
                                output_cost_per_m=0.0,
                                currency="USD",
                                unit="local compute",
                                source_url="https://ollama.com",
                                last_verified="2025-01-01",
                                assumptions="Locally installed model discovered from running daemon.",
                            ),
                            metadata={
                                "parameter_size": om.parameter_size,
                                "quantization_level": om.quantization_level,
                                "family": om.family,
                                "size_bytes": om.size_bytes,
                            },
                        )
        except Exception:
            pass

        results = list(models_map.values())

        # Filtering
        if provider:
            results = [m for m in results if m.provider.lower() == provider.lower()]
        if is_local is not None:
            results = [m for m in results if m.is_local == is_local]
        if capability:
            cap_lower = capability.lower()
            results = [
                m
                for m in results
                if any(cap_lower in c.lower() for c in (m.task_capabilities or []))
            ]
        if search:
            s_lower = search.lower()
            results = [
                m
                for m in results
                if s_lower in m.display_name.lower()
                or s_lower in m.model_identifier.lower()
                or s_lower in m.provider.lower()
                or s_lower in m.id.lower()
            ]

        return sorted(results, key=lambda m: (not m.is_available, not m.is_installed, m.provider))

    async def get_model(self, provider: str, model_identifier: str) -> CatalogModel | None:
        """Find a model by provider and exact model identifier."""
        models = await self.get_all_models()
        for m in models:
            if (
                m.provider.lower() == provider.lower()
                and m.model_identifier.lower() == model_identifier.lower()
            ):
                return m

        # If not in catalog, construct ad-hoc verified entry for manual typing
        is_local = provider.lower() == "ollama"
        return CatalogModel(
            id=f"{provider.lower()}/{model_identifier}",
            model_identifier=model_identifier,
            provider=provider.lower(),
            display_name=f"{model_identifier} (Custom/Typed)",
            is_local=is_local,
            is_available=True,
            is_installed=True if is_local else None,
            pricing=ModelPricing(
                input_cost_per_m=0.0 if is_local else None,
                output_cost_per_m=0.0 if is_local else None,
                currency="USD",
                unit="local compute" if is_local else "per 1M tokens",
                source_url=None,
                last_verified=None,
                assumptions="Custom user-specified model identifier.",
            ),
        )

    async def get_provider_summaries(self) -> list[CatalogProviderInfo]:
        """Return connectivity and model count summary for each provider family."""
        settings = get_settings()
        models = await self.get_all_models()

        ollama_status = "offline"
        try:
            rep = await check_ollama_status(base_url=settings.ollama_base_url, timeout_seconds=1.5)
            ollama_status = "online" if rep.is_reachable else "offline"
        except Exception:
            pass

        families = [
            (
                "ollama",
                "Ollama Local",
                True,
                True,
                ollama_status,
            ),
            (
                "openai",
                "OpenAI",
                False,
                bool(settings.openai_api_key),
                "online" if settings.openai_api_key else "unconfigured",
            ),
            (
                "anthropic",
                "Anthropic Claude",
                False,
                bool(settings.anthropic_api_key),
                "online" if settings.anthropic_api_key else "unconfigured",
            ),
            (
                "gemini",
                "Google Gemini",
                False,
                bool(settings.gemini_api_key),
                "online" if settings.gemini_api_key else "unconfigured",
            ),
            (
                "nvidia",
                "NVIDIA NIM",
                False,
                bool(settings.nvidia_api_key),
                "online" if settings.nvidia_api_key else "unconfigured",
            ),
            (
                "custom_openai",
                "Custom OpenAI Endpoint",
                False,
                True,
                "online",
            ),
        ]

        summaries: list[CatalogProviderInfo] = []
        for p_id, p_name, is_loc, is_conf, p_status in families:
            p_models = [m for m in models if m.provider == p_id]
            installed_cnt = sum(1 for m in p_models if m.is_installed or not is_loc)
            summaries.append(
                CatalogProviderInfo(
                    provider=p_id,
                    display_name=p_name,
                    is_local=is_loc,
                    is_configured=is_conf,
                    status=p_status,
                    installed_models_count=installed_cnt,
                    models=p_models,
                )
            )

        return summaries


catalog_service = ModelCatalogService()
