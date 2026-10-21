"""Abstract Base Provider interface and capability contracts."""

from abc import ABC, abstractmethod
from typing import Any

from src.evalforge.providers.schemas import (
    InferenceRequest,
    InferenceResponse,
    ModelInfo,
    ProviderCapabilities,
)


class BaseProvider(ABC):
    """Abstract interface that all inference providers (Ollama, Mock, Cloud) must implement."""

    def __init__(self, name: str, config: dict[str, Any] | None = None):
        self.name = name
        self.config = config or {}

    @abstractmethod
    async def health_check(self) -> bool:
        """Check whether the inference provider backend is reachable and healthy."""
        pass

    @abstractmethod
    async def list_models(self) -> list[ModelInfo]:
        """List locally or remotely available models."""
        pass

    @abstractmethod
    async def get_model_capabilities(self, model_id: str) -> ProviderCapabilities:
        """Inspect and return verified capabilities for a specific model."""
        pass

    @abstractmethod
    async def generate(self, request: InferenceRequest) -> InferenceResponse:
        """Execute a text or structured inference request."""
        pass

    async def close(self) -> None:  # noqa: B027
        """Release underlying HTTP client or connection resources."""
        pass
