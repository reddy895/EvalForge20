"""Provider registry for looking up and instantiating provider adapters."""

from typing import Any
from app.domain.errors import ProviderError
from app.providers.base import BaseProvider


class ProviderRegistry:
    """Registry for AI model providers."""

    def __init__(self) -> None:
        self._providers: dict[str, type[BaseProvider]] = {}

    def register(self, name: str, provider_cls: type[BaseProvider]) -> None:
        """Register a provider implementation under a unique name."""
        self._providers[name.lower()] = provider_cls

    def get(self, name: str, **kwargs: Any) -> BaseProvider:
        """Instantiate and return a provider by name."""
        key = name.lower()
        if key not in self._providers:
            available = ", ".join(sorted(self._providers.keys()))
            raise ProviderError(f"Unknown provider '{name}'. Available providers: [{available}]")
        return self._providers[key](**kwargs)

    def list_providers(self) -> list[str]:
        """List all registered provider names."""
        return sorted(self._providers.keys())


provider_registry = ProviderRegistry()
