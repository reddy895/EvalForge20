"""Model provider adapters for EvalForge20."""

# Import built-in providers to trigger automatic registration
from app.providers import mock, ollama, ollama_diagnostics
from app.providers.registry import provider_registry

__all__ = [
    "mock",
    "ollama",
    "ollama_diagnostics",
    "provider_registry",
]
