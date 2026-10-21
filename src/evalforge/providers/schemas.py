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


class ModelInfo(BaseModel):
    id: str
    name: str
    provider: str
    size_bytes: int | None = None
    parameter_size: str | None = None
    quantization: str | None = None
    family: str | None = None
    modified_at: str | None = None


class ProviderCapabilities(BaseModel):
    supports_chat: bool = True
    supports_generation: bool = True
    supports_streaming: bool = True
    supports_tools: bool = False
    supports_structured_output: bool = False
    supports_system_prompt: bool = True
    max_context_length: int | None = 4096
