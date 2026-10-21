"""Registry managing inference provider lifecycle and dynamic lookup."""

from collections.abc import Callable
from typing import Any

from src.evalforge.core.errors import ProviderError
from src.evalforge.providers.base import BaseProvider
from src.evalforge.providers.mock import MockProvider
from src.evalforge.providers.ollama.provider import OllamaProvider


class ProviderRegistry:
    """Central registry for registering and resolving inference providers."""

    def __init__(self) -> None:
        self._providers: dict[str, BaseProvider] = {}
        self._factories: dict[str, Callable[[], BaseProvider]] = {}
        self._init_defaults()

    def _init_defaults(self) -> None:
        # Register standard built-in providers
        self.register_factory("ollama", lambda: OllamaProvider())
        self.register_factory("mock", lambda: MockProvider())

    def register(self, name: str, provider: BaseProvider) -> None:
        """Register an active provider instance."""
        self._providers[name.lower()] = provider

    def register_factory(self, name: str, factory: Callable[[], BaseProvider]) -> None:
        """Register a lazy provider constructor."""
        self._factories[name.lower()] = factory

    def get(self, name: str = "ollama") -> BaseProvider:
        """Resolve a provider instance by name (case-insensitive)."""
        key = name.lower()
        if key in self._providers:
            return self._providers[key]

        if key in self._factories:
            instance = self._factories[key]()
            self._providers[key] = instance
            return instance

        raise ProviderError(
            f"Unsupported provider '{name}'. Available providers: {list(self.list_names())}",
            provider=name,
        )

    def list_names(self) -> list[str]:
        """List all registered provider names."""
        return sorted(set(self._providers.keys()) | set(self._factories.keys()))

    async def list_status(self) -> list[dict[str, Any]]:
        """Check and return status for all registered providers."""
        results: list[dict[str, Any]] = []
        for name in self.list_names():
            provider = self.get(name)
            healthy = False
            try:
                healthy = await provider.health_check()
            except Exception:
                healthy = False
            results.append(
                {
                    "name": name,
                    "healthy": healthy,
                    "default": name == "ollama",
                }
            )
        return results

    async def close_all(self) -> None:
        """Close all instantiated providers."""
        for provider in self._providers.values():
            await provider.close()
        self._providers.clear()


_registry_instance: ProviderRegistry | None = None


def get_provider_registry() -> ProviderRegistry:
    """Return singleton provider registry."""
    global _registry_instance
    if _registry_instance is None:
        _registry_instance = ProviderRegistry()
    return _registry_instance
