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
        super().__init__(
            name=name,
            config=config,
            display_name="Ollama (Local)",
            provider_type="local",
            implementation_status="implemented_and_tested",
            setup_instructions="Install Ollama (https://ollama.com) and start it via 'ollama serve'. Pull models using 'ollama pull <name>'.",
        )
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

        # Normalize model identifier (strip ollama: prefix and resolve catalog models)
        model_to_use = request.model
        if model_to_use.startswith("ollama:"):
            model_to_use = model_to_use[7:]
        else:
            try:
                from src.evalforge.services.model_service import VERIFIED_CATALOG_MODELS
                for cm in VERIFIED_CATALOG_MODELS:
                    if cm.id == model_to_use and cm.model_identifier:
                        model_to_use = cm.model_identifier
                        break
            except Exception:
                pass

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
            "model": model_to_use,
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

        wall_duration_ms = (time.perf_counter() - start_time) * 1000

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

        # Precise Ollama nanosecond durations
        total_dur_ns = raw_response.get("total_duration")
        load_dur_ns = raw_response.get("load_duration")
        prompt_eval_dur_ns = raw_response.get("prompt_eval_duration")
        eval_dur_ns = raw_response.get("eval_duration")

        # Calculate genuine tokens per second: completion_tokens / (eval_duration_sec)
        tps: float | None = None
        if completion_tokens and eval_dur_ns and eval_dur_ns > 0:
            tps = round(completion_tokens / (eval_dur_ns / 1e9), 2)
        elif completion_tokens and wall_duration_ms > 0:
            tps = round(completion_tokens / (wall_duration_ms / 1000.0), 2)

        prompt_tps: float | None = None
        if prompt_tokens and prompt_eval_dur_ns and prompt_eval_dur_ns > 0:
            prompt_tps = round(prompt_tokens / (prompt_eval_dur_ns / 1e9), 2)

        # Compute millisecond equivalents
        total_dur_ms = round(total_dur_ns / 1e6, 2) if total_dur_ns is not None else round(wall_duration_ms, 2)
        load_dur_ms = round(load_dur_ns / 1e6, 2) if load_dur_ns is not None else None
        eval_dur_ms = round(eval_dur_ns / 1e6, 2) if eval_dur_ns is not None else None
        prompt_eval_dur_ms = round(prompt_eval_dur_ns / 1e6, 2) if prompt_eval_dur_ns is not None else None

        return InferenceResponse(
            text=response_text,
            model=request.model,
            provider=self.name,
            latency_ms=total_dur_ms,
            usage=token_usage,
            tool_calls=tool_calls,
            raw_metadata={
                "total_duration_ns": total_dur_ns,
                "load_duration_ns": load_dur_ns,
                "prompt_eval_duration_ns": prompt_eval_dur_ns,
                "eval_duration_ns": eval_dur_ns,
                "total_duration_ms": total_dur_ms,
                "load_duration_ms": load_dur_ms,
                "eval_duration_ms": eval_dur_ms,
                "prompt_eval_dur_ms": prompt_eval_dur_ms,
                "tokens_per_second": tps,
                "prompt_tokens_per_second": prompt_tps,
                "wall_latency_ms": round(wall_duration_ms, 2),
                "eval_count": completion_tokens,
                "prompt_eval_count": prompt_tokens,
            },
        )

    async def close(self) -> None:
        await self.client.close()
