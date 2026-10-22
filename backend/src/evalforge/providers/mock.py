"""Deterministic mock provider for hermetic unit testing without external APIs."""

import asyncio
import json
import re
import time
from typing import Any

from src.evalforge.core.errors import ModelNotFoundError, ProviderError
from src.evalforge.providers.base import BaseProvider
from src.evalforge.providers.schemas import (
    InferenceRequest,
    InferenceResponse,
    ModelInfo,
    ProviderCapabilities,
    TokenUsage,
    ToolCall,
)


class MockProvider(BaseProvider):
    """Deterministic mock provider simulating LLM generation, tool calling, and structured outputs."""

    DEFAULT_MODELS = [
        ModelInfo(
            id="mock-llama-3.1-8b",
            name="Mock Llama 3.1 8B Instruct",
            provider="mock",
            size_bytes=4661224576,
            parameter_size="8B",
            quantization="Q4_K_M",
            family="llama",
        ),
        ModelInfo(
            id="mock-qwen-2.5-7b",
            name="Mock Qwen 2.5 7B Instruct",
            provider="mock",
            size_bytes=4434224576,
            parameter_size="7B",
            quantization="Q4_K_M",
            family="qwen2",
        ),
        ModelInfo(
            id="mock-mistral-7b",
            name="Mock Mistral 7B Instruct",
            provider="mock",
            size_bytes=4100224576,
            parameter_size="7B",
            quantization="Q4_K_M",
            family="mistral",
        ),
    ]

    def __init__(
        self,
        name: str = "mock",
        config: dict[str, Any] | None = None,
        healthy: bool = True,
        latency_seconds: float = 0.005,
        canned_responses: dict[str, str] | None = None,
        raise_error: Exception | None = None,
    ):
        super().__init__(
            name=name,
            config=config,
            display_name="Deterministic Mock",
            provider_type="local",
            implementation_status="implemented_and_tested",
            setup_instructions="Built-in hermetic mock provider. No external service or API key required.",
        )
        self.healthy = healthy
        self.latency_seconds = latency_seconds
        self.canned_responses = canned_responses or {}
        self.raise_error = raise_error
        self.call_history: list[InferenceRequest] = []

    async def health_check(self) -> bool:
        return self.healthy

    async def list_models(self) -> list[ModelInfo]:
        if not self.healthy:
            raise ProviderError("Mock provider is offline", provider=self.name)
        return list(self.DEFAULT_MODELS)

    async def get_model_capabilities(self, model_id: str) -> ProviderCapabilities:
        valid_ids = [m.id for m in self.DEFAULT_MODELS]
        if model_id not in valid_ids and not model_id.startswith("mock-"):
            raise ModelNotFoundError(model_id, self.name)
        return ProviderCapabilities(
            supports_chat=True,
            supports_generation=True,
            supports_streaming=True,
            supports_tools=True,
            supports_structured_output=True,
            supports_system_prompt=True,
            max_context_length=8192,
        )

    async def generate(self, request: InferenceRequest) -> InferenceResponse:
        self.call_history.append(request)

        if self.raise_error:
            raise self.raise_error

        if not self.healthy:
            raise ProviderError("Mock provider unavailable", provider=self.name)

        # Validate model
        valid_ids = [m.id for m in self.DEFAULT_MODELS]
        if request.model not in valid_ids and not request.model.startswith("mock-"):
            raise ModelNotFoundError(request.model, self.name)

        if self.latency_seconds > 0:
            await asyncio.sleep(self.latency_seconds)

        start_time = time.perf_counter()

        # Determine prompt text
        prompt_text = request.prompt or ""
        if request.messages:
            prompt_text = " ".join([m.content for m in request.messages])

        # Check canned responses
        response_text = ""
        for pattern, canned in self.canned_responses.items():
            if re.search(pattern, prompt_text, re.IGNORECASE):
                response_text = canned
                break

        # Check tool execution requests
        tool_calls: list[ToolCall] | None = None
        if request.tools and (
            "call tool" in prompt_text.lower() or "use tool" in prompt_text.lower()
        ):
            first_tool = request.tools[0]
            sample_args: dict[str, Any] = {}
            if "properties" in first_tool.parameters:
                for prop_name in first_tool.parameters["properties"]:
                    sample_args[prop_name] = "test_value"
            tool_calls = [ToolCall(name=first_tool.name, arguments=sample_args)]
            response_text = f"Calling tool {first_tool.name} with arguments."

        # Check structured json requests
        elif request.json_schema and not response_text:
            dummy_json: dict[str, Any] = {}
            if "properties" in request.json_schema:
                for prop_name, prop_def in request.json_schema["properties"].items():
                    prop_type = prop_def.get("type", "string")
                    if prop_type == "integer":
                        dummy_json[prop_name] = 42
                    elif prop_type == "boolean":
                        dummy_json[prop_name] = True
                    elif prop_type == "array":
                        dummy_json[prop_name] = ["item_a", "item_b"]
                    else:
                        dummy_json[prop_name] = f"mock_{prop_name}"
            response_text = json.dumps(dummy_json)

        # Fallback default response
        if not response_text:
            response_text = f"Mock response for: {prompt_text[:50]}"

        duration_ms = (time.perf_counter() - start_time) * 1000 + (self.latency_seconds * 1000)

        # Deterministic token estimation
        prompt_tokens = max(1, len(prompt_text.split()))
        completion_tokens = max(1, len(response_text.split()))

        return InferenceResponse(
            text=response_text,
            model=request.model,
            provider=self.name,
            latency_ms=round(duration_ms, 2),
            usage=TokenUsage(
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=prompt_tokens + completion_tokens,
            ),
            tool_calls=tool_calls,
            raw_metadata={"mock": True, "model_id": request.model},
        )
