"""Deterministic mock model provider for reproducible, zero-cost testing and CI."""

import asyncio
import time
from typing import Any

from app.domain.contracts import ProviderRequest, ProviderResponse
from app.domain.errors import NormalizedErrorCategory, classify_exception
from app.providers.base import BaseProvider
from app.providers.registry import provider_registry


class MockProvider(BaseProvider):
    """Deterministic mock provider that simulates model inference without external dependencies."""

    def __init__(
        self,
        model_identifier: str = "mock-model-v1",
        default_response: str = "Mock model response",
        canned_responses: dict[str, str] | None = None,
        simulated_latency_ms: float = 5.0,
        simulated_tokens: dict[str, int] | None = None,
        fail_on_prompts: dict[str, Any] | None = None,
        is_healthy: bool = True,
        timeout_seconds: float = 60.0,
    ):
        super().__init__(provider_name="mock", timeout_seconds=timeout_seconds)
        self.model_identifier = model_identifier
        self.default_response = default_response
        self.canned_responses = canned_responses or {}
        self.simulated_latency_ms = simulated_latency_ms
        self.simulated_tokens = (
            simulated_tokens
            if simulated_tokens is not None
            else {"prompt_tokens": 10, "completion_tokens": 15, "total_tokens": 25}
        )
        self.fail_on_prompts = fail_on_prompts or {}
        self.is_healthy = is_healthy

    async def health_check(self) -> bool:
        return self.is_healthy

    async def list_models(self) -> list[str]:
        return [self.model_identifier, "mock-chat-v1", "mock-agent-v1"]

    async def generate(self, request: ProviderRequest) -> ProviderResponse:
        async def _run() -> ProviderResponse:
            start_time = time.perf_counter()

            # Simulate latency
            if self.simulated_latency_ms > 0:
                await asyncio.sleep(self.simulated_latency_ms / 1000.0)

            prompt = request.prompt

            # Check for configured simulated failures
            for fail_key, err in self.fail_on_prompts.items():
                if fail_key in prompt:
                    latency = round((time.perf_counter() - start_time) * 1000.0, 2)
                    if isinstance(err, NormalizedErrorCategory):
                        return ProviderResponse(
                            output_text=None,
                            latency_ms=latency,
                            error_category=err.value,
                            error_message=f"Simulated {err.value} error for prompt '{fail_key}'",
                            is_success=False,
                        )
                    cat, msg = classify_exception(
                        err if isinstance(err, Exception) else RuntimeError(str(err))
                    )
                    return ProviderResponse(
                        output_text=None,
                        latency_ms=latency,
                        error_category=cat.value,
                        error_message=msg,
                        is_success=False,
                    )

            # Match canned responses
            output_text = self.default_response
            for key, resp in self.canned_responses.items():
                if key in prompt:
                    output_text = resp
                    break

            elapsed_ms = round((time.perf_counter() - start_time) * 1000.0, 2)
            return ProviderResponse(
                output_text=output_text,
                latency_ms=elapsed_ms,
                token_usage=self.simulated_tokens,
                raw_response={"mock_model": self.model_identifier, "simulated": True},
                is_success=True,
            )

        return await self.execute_with_guard(request, _run)


provider_registry.register("mock", MockProvider)
