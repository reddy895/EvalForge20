"""Pydantic schemas for inference requests, responses, models, and capabilities."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    role: str  # "system", "user", "assistant", "tool"
    content: str


class ToolDefinition(BaseModel):
    name: str
    description: str
    parameters: Dict[str, Any] = Field(default_factory=dict)


class ToolCall(BaseModel):
    name: str
    arguments: Dict[str, Any] = Field(default_factory=dict)


class InferenceRequest(BaseModel):
    model: str
    prompt: Optional[str] = None
    messages: Optional[List[ChatMessage]] = None
    system_prompt: Optional[str] = None
    temperature: float = 0.7
    top_p: Optional[float] = None
    seed: Optional[int] = None
    context_length: Optional[int] = None
    max_tokens: Optional[int] = None
    json_schema: Optional[Dict[str, Any]] = None
    tools: Optional[List[ToolDefinition]] = None
    stop: Optional[List[str]] = None


class TokenUsage(BaseModel):
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    total_tokens: Optional[int] = None


class InferenceResponse(BaseModel):
    text: str
    model: str
    provider: str
    latency_ms: float
    usage: Optional[TokenUsage] = None
    tool_calls: Optional[List[ToolCall]] = None
    raw_metadata: Dict[str, Any] = Field(default_factory=dict)


class ModelInfo(BaseModel):
    id: str
    name: str
    provider: str
    size_bytes: Optional[int] = None
    parameter_size: Optional[str] = None
    quantization: Optional[str] = None
    family: Optional[str] = None
    modified_at: Optional[str] = None


class ProviderCapabilities(BaseModel):
    supports_chat: bool = True
    supports_generation: bool = True
    supports_streaming: bool = True
    supports_tools: bool = False
    supports_structured_output: bool = False
    supports_system_prompt: bool = True
    max_context_length: Optional[int] = 4096
