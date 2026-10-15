"""Base provider adapter defining the neutral provider interface, normalization, and timeout handling."""

import asyncio
import time
from abc import abstractmethod
from collections.abc import Awaitable, Callable
from typing import Any

import httpx

from app.config import get_settings
from app.domain.contracts import ProviderContract, ProviderRequest, ProviderResponse
from app.domain.errors import NormalizedErrorCategory, classify_exception


def normalize_token_usage(raw_usage: dict[str, Any] | None) -> dict[str, int] | None:
    """Normalize vendor-specific token usage dictionary into standard keys."""
    if not raw_usage:
        return None

    # Handle Ollama keys: eval_count, prompt_eval_count
    # Handle OpenAI keys: prompt_tokens, completion_tokens, total_tokens
    prompt_tokens = (
        raw_usage.get("prompt_tokens")
        or raw_usage.get("prompt_eval_count")
        or raw_usage.get("input_tokens")
    )
    completion_tokens = (
        raw_usage.get("completion_tokens")
        or raw_usage.get("eval_count")
        or raw_usage.get("output_tokens")
    )

    total_tokens = raw_usage.get("total_tokens")
    if total_tokens is None and prompt_tokens is not None and completion_tokens is not None:
        total_tokens = prompt_tokens + completion_tokens

    normalized: dict[str, int] = {}
    if prompt_tokens is not None:
        normalized["prompt_tokens"] = int(prompt_tokens)
    if completion_tokens is not None:
        normalized["completion_tokens"] = int(completion_tokens)
    if total_tokens is not None:
        normalized["total_tokens"] = int(total_tokens)

    return normalized if normalized else None


def truncate_output_if_exceeds(text: str | None) -> tuple[str | None, bool]:
    """Truncate output if it exceeds maximum allowed response bytes."""
    if text is None:
        return None, False

    settings = get_settings()
    max_bytes = settings.max_output_bytes
    encoded = text.encode("utf-8")
    if len(encoded) > max_bytes:
        truncated = encoded[:max_bytes].decode("utf-8", errors="ignore")
        return truncated + "\n...[TRUNCATED_MAX_BYTES_EXCEEDED]", True
    return text, False


class BaseProvider(ProviderContract):
    """Abstract base class for all LLM and agent execution providers."""

    def __init__(self, provider_name: str, timeout_seconds: float = 60.0):
        self.provider_name = provider_name
        self.timeout_seconds = timeout_seconds

    @abstractmethod
    async def generate(self, request: ProviderRequest) -> ProviderResponse:
        """Execute a prompt request and return normalized response."""
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """Verify provider availability and network connectivity."""
        pass

    async def list_models(self) -> list[str]:
        """Return a list of available model identifiers supported by this provider."""
        return []

    async def execute_with_guard(
        self,
        request: ProviderRequest,
        action: Callable[[], Awaitable[ProviderResponse]],
    ) -> ProviderResponse:
        """Execute a provider call wrapped with timeout, error classification, and output truncation."""
        start_time = time.perf_counter()
        timeout = request.extra_params.get("timeout_seconds") or self.timeout_seconds

        try:
            async with asyncio.timeout(timeout):
                resp = await action()
                # Ensure output bounds
                clean_text, was_truncated = truncate_output_if_exceeds(resp.output_text)
                return ProviderResponse(
                    output_text=clean_text,
                    latency_ms=resp.latency_ms,
                    token_usage=normalize_token_usage(resp.token_usage),
                    raw_response=resp.raw_response,
                    error_category=resp.error_category,
                    error_message=resp.error_message,
                    is_success=resp.is_success,
                )

        except TimeoutError:
            elapsed = round((time.perf_counter() - start_time) * 1000.0, 2)
            return ProviderResponse(
                output_text=None,
                latency_ms=elapsed,
                error_category=NormalizedErrorCategory.TIMEOUT.value,
                error_message=f"Request to {self.provider_name} timed out after {timeout}s",
                is_success=False,
            )
        except httpx.ConnectError as exc:
            elapsed = round((time.perf_counter() - start_time) * 1000.0, 2)
            return ProviderResponse(
                output_text=None,
                latency_ms=elapsed,
                error_category=NormalizedErrorCategory.PROVIDER_UNAVAILABLE.value,
                error_message=f"Cannot connect to {self.provider_name}: {exc}",
                is_success=False,
            )
        except httpx.HTTPStatusError as exc:
            elapsed = round((time.perf_counter() - start_time) * 1000.0, 2)
            status = exc.response.status_code
            if status in (401, 403):
                cat = NormalizedErrorCategory.AUTHENTICATION_ERROR
            elif status == 429:
                cat = NormalizedErrorCategory.RATE_LIMIT
            elif status >= 500:
                cat = NormalizedErrorCategory.PROVIDER_UNAVAILABLE
            else:
                cat = NormalizedErrorCategory.EXECUTION_ERROR

            return ProviderResponse(
                output_text=None,
                latency_ms=elapsed,
                error_category=cat.value,
                error_message=f"HTTP {status} error from {self.provider_name}: {exc.response.text[:200]}",
                is_success=False,
            )
        except Exception as exc:
            elapsed = round((time.perf_counter() - start_time) * 1000.0, 2)
            cat, msg = classify_exception(exc)
            return ProviderResponse(
                output_text=None,
                latency_ms=elapsed,
                error_category=cat.value,
                error_message=msg,
                is_success=False,
            )
