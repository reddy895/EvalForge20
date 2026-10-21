"""API schemas for provider discovery, health checks, and test executions."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from src.evalforge.providers.schemas import ModelInfo, TokenUsage


class ProviderStatusItem(BaseModel):
    name: str
    healthy: bool
    default: bool


class ProvidersListResponse(BaseModel):
    providers: List[ProviderStatusItem]


class OllamaHealthCheckResponse(BaseModel):
    status: str
    base_url: str
    reachable: bool
    version: Optional[str] = None
    suggestion: Optional[str] = None


class OllamaModelsListResponse(BaseModel):
    total: int
    models: List[ModelInfo]


class OllamaTestInferenceRequest(BaseModel):
    model: str = Field(..., description="Name of the locally installed Ollama model (e.g. 'llama3.2')")
    prompt: str = Field(default="Say hello and confirm you are operational.", description="Test prompt to execute")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    system_prompt: Optional[str] = None


class OllamaTestInferenceResponse(BaseModel):
    success: bool
    model: str
    text: str
    latency_ms: float
    usage: Optional[TokenUsage] = None
    raw_metadata: Dict[str, Any] = Field(default_factory=dict)
