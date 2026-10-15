"""Model provider adapters for EvalForge20."""

# Import built-in providers to trigger automatic registration
from app.providers import mock, ollama
from app.providers.registry import provider_registry

__all__ = [
    "mock",
    "ollama",
    "provider_registry",
]
