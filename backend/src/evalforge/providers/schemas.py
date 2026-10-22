"""Pydantic schemas for inference requests, responses, models, and capabilities."""

from typing import Any

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    role: str  # "system", "user", "assistant", "tool"
    content: str


class ToolDefinition(BaseModel):
    name: str
    description: str
    parameters: dict[str, Any] = Field(default_factory=dict)


class ToolCall(BaseModel):
    name: str
    arguments: dict[str, Any] = Field(default_factory=dict)


class InferenceRequest(BaseModel):
    model: str
    prompt: str | None = None
    messages: list[ChatMessage] | None = None
    system_prompt: str | None = None
    temperature: float = 0.7
    top_p: float | None = None
    seed: int | None = None
    context_length: int | None = None
    max_tokens: int | None = None
    json_schema: dict[str, Any] | None = None
    tools: list[ToolDefinition] | None = None
    stop: list[str] | None = None


class TokenUsage(BaseModel):
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    total_tokens: int | None = None


class InferenceResponse(BaseModel):
    text: str
    model: str
    provider: str
    latency_ms: float
    usage: TokenUsage | None = None
    tool_calls: list[ToolCall] | None = None
    raw_metadata: dict[str, Any] = Field(default_factory=dict)


class BenchmarkScoreItem(BaseModel):
    benchmark_name: str
    metric: str
    score: float
    source: str
    verified: bool = True


class HardwareRequirements(BaseModel):
    min_ram_gb: float
    recommended_ram_gb: float
    min_vram_gb: float | None = None
    quantization: str = "Q4_K_M"
    context_length: int = 4096
    disk_space_gb: float = 4.0


class ModelPricingItem(BaseModel):
    input_cost_per_m: float | None = 0.0
    output_cost_per_m: float | None = 0.0
    currency: str = "USD"
    unit: str = "1M tokens"
    is_free_local: bool = True
    source_url: str | None = None


class ModelInfo(BaseModel):
    id: str
    name: str
    provider: str
    model_identifier: str | None = None
    size_bytes: int | None = None
    parameter_size: str | None = None
    parameter_count: str | None = None
    quantization: str | None = None
    family: str | None = None
    context_window: int = 4096
    modalities: list[str] = Field(default_factory=lambda: ["text->text"])
    supports_tools: bool = False
    supports_structured_output: bool = False
    license: str | None = "Unknown"
    is_commercial_use_allowed: bool = True
    release_date: str | None = None
    description: str | None = None
    is_local: bool = True
    is_installed: bool = False
    is_remote: bool = False
    benchmarks: list[BenchmarkScoreItem] = Field(default_factory=list)
    measured_latency_ms: float | None = None
    measured_throughput_tok_s: float | None = None
    pricing: ModelPricingItem = Field(default_factory=ModelPricingItem)
    hardware: HardwareRequirements = Field(
        default_factory=lambda: HardwareRequirements(
            min_ram_gb=8.0, recommended_ram_gb=16.0, disk_space_gb=4.5
        )
    )
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    recommended_tasks: list[str] = Field(default_factory=list)
    unsuitable_tasks: list[str] = Field(default_factory=list)
    modified_at: str | None = None


class ProviderCapabilities(BaseModel):
    supports_chat: bool = True
    supports_generation: bool = True
    supports_streaming: bool = True
    supports_tools: bool = False
    supports_structured_output: bool = False
    supports_system_prompt: bool = True
    max_context_length: int | None = 4096


class ProviderInfo(BaseModel):
    name: str
    display_name: str
    provider_type: str  # "local" | "cloud"
    implementation_status: str  # "implemented_and_tested" | "configurable_cloud" | "planned"
    healthy: bool
    is_configured: bool
    default: bool = False
    base_url: str | None = None
    setup_instructions: str | None = None
    supported_models_count: int = 0
    capabilities: ProviderCapabilities = Field(default_factory=ProviderCapabilities)

