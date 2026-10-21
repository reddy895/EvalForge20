"""Ollama provider implementation adhering to BaseProvider interface."""

import json
import time
from typing import Any

from src.evalforge.providers.base import BaseProvider
from src.evalforge.providers.ollama.capabilities import detect_capabilities, parse_model_info
from src.evalforge.providers.ollama.client import OllamaClient, get_ollama_client
from src.evalforge.providers.schemas import (
    InferenceRequest,
    InferenceResponse,
    ModelInfo,
    ProviderCapabilities,
    TokenUsage,
    ToolCall,
)


class OllamaProvider(BaseProvider):
    """Local Ollama inference provider with tool calling and structured output support."""

    def __init__(
        self,
        name: str = "ollama",
        config: dict[str, Any] | None = None,
        client: OllamaClient | None = None,
    ):
        super().__init__(name=name, config=config)
        self.client = client or get_ollama_client(base_url=self.config.get("base_url"))

    async def health_check(self) -> bool:
        return await self.client.check_health()

    async def list_models(self) -> list[ModelInfo]:
        raw_data = await self.client.list_tags()
        models_raw = raw_data.get("models", [])
        return [parse_model_info(item) for item in models_raw]

    async def get_model_capabilities(self, model_id: str) -> ProviderCapabilities:
        show_data = await self.client.show_model(model_id)
        return detect_capabilities(show_data, model_id)

    async def generate(self, request: InferenceRequest) -> InferenceResponse:
        start_time = time.perf_counter()

        options: dict[str, Any] = {
            "temperature": request.temperature,
        }
        if request.top_p is not None:
            options["top_p"] = request.top_p
        if request.seed is not None:
            options["seed"] = request.seed
        if request.context_length is not None:
            options["num_ctx"] = request.context_length
        if request.max_tokens is not None:
            options["num_predict"] = request.max_tokens
        if request.stop:
            options["stop"] = request.stop

        # Build payload
        payload: dict[str, Any] = {
            "model": request.model,
            "options": options,
        }

        # Handle structured outputs
        if request.json_schema:
            payload["format"] = request.json_schema

        # Execute either Chat or Generation endpoint
        use_chat = bool(request.messages or request.tools or request.system_prompt)

        raw_response: dict[str, Any]
        tool_calls: list[ToolCall] | None = None
        response_text = ""

        if use_chat:
            messages: list[dict[str, Any]] = []
            if request.system_prompt:
                messages.append({"role": "system", "content": request.system_prompt})
            if request.messages:
                for msg in request.messages:
                    messages.append({"role": msg.role, "content": msg.content})
            elif request.prompt:
                messages.append({"role": "user", "content": request.prompt})

            payload["messages"] = messages

            if request.tools:
                payload["tools"] = [
                    {
                        "type": "function",
                        "function": {
                            "name": t.name,
                            "description": t.description,
                            "parameters": t.parameters,
                        },
                    }
                    for t in request.tools
                ]

            raw_response = await self.client.chat(payload)
            msg = raw_response.get("message", {})
            response_text = msg.get("content", "")

            # Extract tool calls if returned
            if "tool_calls" in msg and msg["tool_calls"]:
                tool_calls = []
                for tc in msg["tool_calls"]:
                    func = tc.get("function", {})
                    args = func.get("arguments", {})
                    if isinstance(args, str):
                        try:
                            args = json.loads(args)
                        except Exception:
                            args = {"raw": args}
                    tool_calls.append(ToolCall(name=func.get("name", "unknown"), arguments=args))
        else:
            payload["prompt"] = request.prompt or ""
            raw_response = await self.client.generate(payload)
            response_text = raw_response.get("response", "")

        duration_ms = (time.perf_counter() - start_time) * 1000

        # Extract token usage if provided by Ollama
        prompt_tokens = raw_response.get("prompt_eval_count")
        completion_tokens = raw_response.get("eval_count")
        token_usage = None
        if prompt_tokens is not None or completion_tokens is not None:
            p_tok = prompt_tokens or 0
            c_tok = completion_tokens or 0
            token_usage = TokenUsage(
                prompt_tokens=p_tok,
                completion_tokens=c_tok,
                total_tokens=p_tok + c_tok,
            )

        return InferenceResponse(
            text=response_text,
            model=request.model,
            provider=self.name,
            latency_ms=round(duration_ms, 2),
            usage=token_usage,
            tool_calls=tool_calls,
            raw_metadata={
                "total_duration_ns": raw_response.get("total_duration"),
                "load_duration_ns": raw_response.get("load_duration"),
                "prompt_eval_duration_ns": raw_response.get("prompt_eval_duration"),
                "eval_duration_ns": raw_response.get("eval_duration"),
            },
        )

    async def close(self) -> None:
        await self.client.close()
