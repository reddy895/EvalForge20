"""API schemas for provider discovery, health checks, and test executions."""

from typing import Any

from pydantic import BaseModel, Field

from src.evalforge.providers.schemas import ModelInfo, TokenUsage


class ProviderStatusItem(BaseModel):
    name: str
    healthy: bool
    default: bool


class ProvidersListResponse(BaseModel):
    providers: list[ProviderStatusItem]


class OllamaHealthCheckResponse(BaseModel):
    status: str
    base_url: str
    reachable: bool
    connectivity_state: str = "reachable"
    version: str | None = None
    installed_locally: bool = False
    installed_models_count: int = 0
    available_models: list[str] = Field(default_factory=list)
    model_ready: bool = False
    suggestion: str | None = None
    last_checked_at: str | None = None


class OllamaModelsListResponse(BaseModel):
    total: int
    models: list[ModelInfo]


class OllamaTestInferenceRequest(BaseModel):
    model: str = Field(
        ..., description="Name of the locally installed Ollama model (e.g. 'llama3.2')"
    )
    prompt: str = Field(
        default="Say hello and confirm you are operational.", description="Test prompt to execute"
    )
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    system_prompt: str | None = None


class OllamaTestInferenceResponse(BaseModel):
    success: bool
    model: str
    text: str
    latency_ms: float
    usage: TokenUsage | None = None
    raw_metadata: dict[str, Any] = Field(default_factory=dict)
