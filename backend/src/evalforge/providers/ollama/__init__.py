"""Ollama local inference provider integration."""

from src.evalforge.providers.ollama.client import OllamaClient, get_ollama_client
from src.evalforge.providers.ollama.provider import OllamaProvider

_ollama_provider: OllamaProvider | None = None


def get_ollama_provider(base_url: str | None = None) -> OllamaProvider:
    """Return singleton Ollama provider instance."""
    global _ollama_provider
    if _ollama_provider is None or (base_url and _ollama_provider.config.get("base_url") != base_url):
        config = {"base_url": base_url} if base_url else {}
        _ollama_provider = OllamaProvider(name="ollama", config=config)
    return _ollama_provider


__all__ = [
    "OllamaProvider",
    "OllamaClient",
    "get_ollama_client",
    "get_ollama_provider",
]
