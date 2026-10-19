"""Schemas for task suitability recommendations and hardware-aware matching."""

from pydantic import BaseModel, Field


class TaskRecommendationRequest(BaseModel):
    task: str = Field(
        ...,
        description="Target task, e.g. 'coding', 'reasoning', 'structured_json', 'rag', 'agent'",
    )
    prefer_local: bool = Field(default=True, description="Prioritize local Ollama models")
    max_ram_gb: float | None = Field(default=None, description="System RAM limit in GB")
    has_gpu: bool = Field(default=False)
    max_vram_gb: float | None = Field(default=None)


class ModelRecommendation(BaseModel):
    model_id: str
    model_name: str
    provider: str
    match_score: float = Field(
        ..., ge=0.0, le=100.0, description="Overall task suitability score (0-100)"
    )
    is_local: bool
    is_installed: bool
    hardware_fit: str  # "Runs locally smoothly", "Requires cloud execution", "Tight fit on memory"
    recommendation_reason: str
    key_evidence: list[str]
    important_tradeoffs: list[str]
    evidence_source: str  # "Verified Benchmark", "Local Evaluation", "Capability Mapping"


class TaskRecommendationResponse(BaseModel):
    task: str
    evaluated_criteria: list[str]
    recommendations: list[ModelRecommendation]
    explanation: str


class HardwareProfileInput(BaseModel):
    os_name: str = "Linux"
    total_ram_gb: float = 16.0
    has_gpu: bool = False
    gpu_name: str | None = None
    vram_gb: float | None = None
    disk_space_gb: float = 20.0
    preferred_tradeoff: str = "balanced"  # "speed", "quality", "balanced"
