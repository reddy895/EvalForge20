"""Domain models and schemas for the unified model catalog and pricing lookup."""

from pydantic import BaseModel, Field


class ModelPricing(BaseModel):
    """Verified token pricing metadata for a model."""

    input_cost_per_m: float | None = Field(
        default=None, description="Input price in USD per 1M tokens"
    )
    output_cost_per_m: float | None = Field(
        default=None, description="Output price in USD per 1M tokens"
    )
    cached_input_cost_per_m: float | None = Field(
        default=None, description="Cached prompt input price in USD per 1M tokens"
    )
    currency: str = Field(default="USD", description="Billing currency")
    unit: str = Field(default="per 1M tokens", description="Pricing calculation unit")
    source_url: str | None = Field(default=None, description="Official documentation source URL")
    last_verified: str | None = Field(
        default=None, description="ISO timestamp when pricing was verified"
    )
    assumptions: str | None = Field(
        default=None, description="Pricing tier, prompt length thresholds, or assumptions"
    )


class CatalogModel(BaseModel):
    """Unified representation of a model in the evaluation catalog."""

    id: str = Field(..., description="Unique slug or identifier, e.g. openai/gpt-4o")
    model_identifier: str = Field(..., description="Exact string sent to provider API, e.g. gpt-4o")
    provider: str = Field(
        ..., description="Provider slug: openai, anthropic, gemini, nvidia, ollama, custom_openai"
    )
    display_name: str = Field(..., description="Human-friendly label")
    is_local: bool = Field(default=False, description="True for local Ollama / offline models")
    is_available: bool = Field(
        default=False, description="True if credentials/daemon are online and ready"
    )
    is_installed: bool | None = Field(
        default=None, description="For local models, whether it is currently downloaded/installed"
    )
    context_window: int | None = Field(default=None, description="Maximum context window tokens")
    modalities: list[str] = Field(default_factory=lambda: ["text->text"])
    supports_tools: bool | None = Field(
        default=None, description="Whether tool/function calling is verified"
    )
    supports_structured_output: bool | None = Field(
        default=None, description="Whether JSON schema / structured output is verified"
    )
    release_date: str | None = Field(
        default=None, description="Release date or model version date (YYYY-MM-DD)"
    )
    task_capabilities: list[str] = Field(
        default_factory=list,
        description="Supported tasks: reasoning, coding, data_extraction, classification, summarization, etc.",
    )
    pricing: ModelPricing | None = Field(default=None)
    metadata: dict[str, str | int | float | bool | None] = Field(default_factory=dict)


class CatalogProviderInfo(BaseModel):
    """Summary of a provider family and its connection state."""

    provider: str
    display_name: str
    is_local: bool
    is_configured: bool
    status: str  # online, offline, unconfigured
    installed_models_count: int
    models: list[CatalogModel] = Field(default_factory=list)
