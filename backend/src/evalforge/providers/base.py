"""Abstract Base Provider interface and capability contracts."""

from abc import ABC, abstractmethod
from typing import Any

from src.evalforge.providers.schemas import (
    InferenceRequest,
    InferenceResponse,
    ModelInfo,
    ProviderCapabilities,
    ProviderInfo,
)


class BaseProvider(ABC):
    """Abstract interface that all inference providers (Ollama, Mock, Cloud) must implement."""

    def __init__(
        self,
        name: str,
        config: dict[str, Any] | None = None,
        display_name: str | None = None,
        provider_type: str = "cloud",
        implementation_status: str = "configurable_cloud",
        setup_instructions: str | None = None,
    ):
        self.name = name
        self.config = config or {}
        self.display_name = display_name or name.title()
        self.provider_type = provider_type
        self.implementation_status = implementation_status
        self.setup_instructions = setup_instructions

    @property
    def is_configured(self) -> bool:
        """Indicate whether the provider has required API keys or endpoints set."""
        return True

    async def get_provider_info(self) -> ProviderInfo:
        """Return standardized operational information and health state."""
        healthy = False
        try:
            healthy = await self.health_check()
        except Exception:
            healthy = False

        models_count = 0
        try:
            models = await self.list_models()
            models_count = len(models)
        except Exception:
            models_count = 0

        caps = ProviderCapabilities()
        try:
            caps = await self.get_model_capabilities("")
        except Exception:
            pass

        return ProviderInfo(
            name=self.name,
            display_name=self.display_name,
            provider_type=self.provider_type,
            implementation_status=self.implementation_status,
            healthy=healthy,
            is_configured=self.is_configured,
            default=self.name == "ollama",
            base_url=self.config.get("base_url"),
            setup_instructions=self.setup_instructions,
            supported_models_count=models_count,
            capabilities=caps,
        )

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
