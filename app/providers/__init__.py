"""Model provider adapters for EvalForge20."""

# Import built-in providers to trigger automatic registration
from app.providers import (
    anthropic,
    custom_openai,
    gemini,
    mock,
    nvidia,
    ollama,
    ollama_diagnostics,
    openai,
)
from app.providers.registry import provider_registry

__all__ = [
    "anthropic",
    "custom_openai",
    "gemini",
    "mock",
    "nvidia",
    "ollama",
    "ollama_diagnostics",
    "openai",
    "provider_registry",
]
