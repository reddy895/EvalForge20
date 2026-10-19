"""Model catalog, capability, benchmark, and hardware schemas."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ModelPricing(BaseModel):
    """Token pricing and compute cost metrics."""

    input_cost_per_m: float | None = Field(
        default=None, description="Input cost in USD per 1M tokens"
    )
    output_cost_per_m: float | None = Field(
        default=None, description="Output cost in USD per 1M tokens"
    )
    currency: str = "USD"
    unit: str = "per 1M tokens"
    is_free_local: bool = False
    source_url: str | None = None


class HardwareRequirements(BaseModel):
    """Estimated hardware and memory requirements."""

    min_ram_gb: float = Field(..., description="Minimum system RAM in GB")
    recommended_ram_gb: float = Field(..., description="Recommended system RAM in GB")
    min_vram_gb: float | None = Field(
        default=None, description="Minimum GPU VRAM in GB if GPU used"
    )
    quantization: str = "4-bit (Q4_K_M)"
    context_length: int = 8192
    disk_space_gb: float = 4.0


class BenchmarkResult(BaseModel):
    """Verified benchmark score with provenance."""

    benchmark_name: str
    metric: str
    score: float
    sample_size: int | None = None
    date_evaluated: str | None = None
    source: str
    is_local_measurement: bool = False


class ModelProfile(BaseModel):
    """Comprehensive intelligence profile for an AI model."""

    id: str
    name: str
    provider: str
    model_identifier: str
    family: str
    architecture: str | None = None
    parameter_count: str | None = None
    size_bytes: int | None = None
    quantization: str | None = None
    context_window: int = 8192
    modalities: list[str] = Field(default_factory=lambda: ["text->text"])
    supports_tools: bool = False
    supports_structured_output: bool = False
    license: str
    is_commercial_use_allowed: bool = True
    release_date: str | None = None
    description: str

    # Status
    is_local: bool = False
    is_installed: bool = False
    installed_size_bytes: int | None = None

    # Performance & Intelligence
    benchmarks: list[BenchmarkResult] = Field(default_factory=list)
    measured_latency_ms: float | None = None
    measured_throughput_tok_s: float | None = None
    pricing: ModelPricing | None = None
    hardware: HardwareRequirements

    # Strengths, Weaknesses & Suitability
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    recommended_tasks: list[str] = Field(default_factory=list)
    unsuitable_tasks: list[str] = Field(default_factory=list)

    metadata: dict[str, Any] = Field(default_factory=dict)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class ModelSummary(BaseModel):
    """Lightweight summary card for catalog browsing and search."""

    id: str
    name: str
    provider: str
    model_identifier: str
    family: str
    parameter_count: str | None = None
    context_window: int
    is_local: bool
    is_installed: bool
    supports_tools: bool
    supports_structured_output: bool
    license: str
    hardware_min_ram_gb: float
    recommended_tasks: list[str]
    headline_benchmark_score: float | None = None
    headline_benchmark_name: str | None = None
    pricing_summary: str = "Free (Local)"


class OllamaModelPullRequest(BaseModel):
    model: str = Field(..., description="Ollama model tag to pull, e.g. 'qwen2.5:3b'")


class OllamaModelPullResponse(BaseModel):
    model: str
    status: str
    message: str


class OllamaStatusReport(BaseModel):
    is_reachable: bool
    base_url: str
    version: str | None = None
    installed_models: list[str] = Field(default_factory=list)
    models_count: int = 0
    status_label: str = "offline"
    latency_ms: float | None = None
    error_message: str | None = None
    setup_instructions: list[str] = Field(default_factory=list)
