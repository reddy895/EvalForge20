"""Model provider adapters for EvalForge20."""

# Import built-in providers to trigger automatic registration
from app.providers import anthropic, gemini, mock, ollama, ollama_diagnostics, openai
from app.providers.registry import provider_registry

__all__ = [
    "anthropic",
    "gemini",
    "mock",
    "ollama",
    "ollama_diagnostics",
    "openai",
    "provider_registry",
]
