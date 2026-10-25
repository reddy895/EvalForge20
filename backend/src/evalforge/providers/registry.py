"""Registry managing inference provider lifecycle and dynamic lookup."""

from collections.abc import Callable
from typing import Any

from src.evalforge.core.errors import ProviderError
from src.evalforge.providers.adapters import (
    AnthropicProvider,
    AzureOpenAIProvider,
    BedrockProvider,
    CohereProvider,
    DeepSeekProvider,
    FireworksProvider,
    GeminiProvider,
    GroqProvider,
    HuggingFaceProvider,
    MistralProvider,
    OpenAIProvider,
    TogetherProvider,
)
from src.evalforge.providers.base import BaseProvider
from src.evalforge.providers.mock import MockProvider
from src.evalforge.providers.ollama.provider import OllamaProvider
from src.evalforge.providers.openai_compatible import OpenAICompatibleProvider
from src.evalforge.providers.schemas import ProviderInfo


class ProviderRegistry:
    """Central registry for registering and resolving inference providers."""

    def __init__(self) -> None:
        self._providers: dict[str, BaseProvider] = {}
        self._factories: dict[str, Callable[[], BaseProvider]] = {}
        self._init_defaults()

    def _init_defaults(self) -> None:
        # 1. Local and Mock providers
        self.register_factory("ollama", lambda: OllamaProvider())
        self.register_factory("mock", lambda: MockProvider())

        # 2. Generic OpenAI-compatible
        self.register_factory("openai_compatible", lambda: OpenAICompatibleProvider())

        # 3. Frontier and Cloud LLM providers
        self.register_factory("openai", lambda: OpenAIProvider())
        self.register_factory("anthropic", lambda: AnthropicProvider())
        self.register_factory("gemini", lambda: GeminiProvider())
        self.register_factory("groq", lambda: GroqProvider())
        self.register_factory("mistral", lambda: MistralProvider())
        self.register_factory("cohere", lambda: CohereProvider())
        self.register_factory("together", lambda: TogetherProvider())
        self.register_factory("fireworks", lambda: FireworksProvider())
        self.register_factory("deepseek", lambda: DeepSeekProvider())
        self.register_factory("huggingface", lambda: HuggingFaceProvider())
        self.register_factory("azure", lambda: AzureOpenAIProvider())
        self.register_factory("bedrock", lambda: BedrockProvider())

    def register(self, name: str, provider: BaseProvider) -> None:
        """Register an active provider instance."""
        self._providers[name.lower()] = provider

    def register_factory(self, name: str, factory: Callable[[], BaseProvider]) -> None:
        """Register a lazy provider constructor."""
        self._factories[name.lower()] = factory

    def get(self, name: str = "ollama") -> BaseProvider:
        """Resolve a provider instance by name (case-insensitive)."""
        key = name.lower().strip()
        aliases: dict[str, str] = {
            "alibaba": "ollama",
            "alibaba / qwen": "ollama",
            "qwen": "ollama",
            "meta": "ollama",
            "meta / llama": "ollama",
            "google": "gemini",
            "google gemini": "gemini",
            "azure_openai": "azure",
            "aws_bedrock": "bedrock",
            "local": "ollama",
        }
        key = aliases.get(key, key)

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

    def list_providers(self) -> dict[str, BaseProvider]:
        """Return a dictionary of all registered and initialized provider instances."""
        for name in self.list_names():
            if name not in self._providers:
                self.get(name)
        return dict(self._providers)

    async def list_status(self) -> list[dict[str, Any]]:
        """Check and return lightweight status for all registered providers (backwards compatible)."""
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
                    "display_name": getattr(provider, "display_name", name.title()),
                    "provider_type": getattr(provider, "provider_type", "cloud"),
                    "implementation_status": getattr(provider, "implementation_status", "configurable_cloud"),
                    "is_configured": getattr(provider, "is_configured", True),
                    "healthy": healthy,
                    "default": name == "ollama",
                }
            )
        return results

    async def list_details(self) -> list[ProviderInfo]:
        """Check and return comprehensive operational metadata and health for all providers."""
        infos: list[ProviderInfo] = []
        for name in self.list_names():
            provider = self.get(name)
            info = await provider.get_provider_info()
            infos.append(info)
        return infos

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
