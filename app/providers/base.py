"""Base provider adapter defining the neutral provider interface."""

from abc import abstractmethod

from app.domain.contracts import ProviderContract, ProviderRequest, ProviderResponse


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
