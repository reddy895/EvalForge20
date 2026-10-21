"""Model capability detection and metadata parser for Ollama."""

from typing import Any, Dict
from src.evalforge.providers.schemas import ModelInfo, ProviderCapabilities

# Known families with robust native tool-calling template support in Ollama
TOOL_CAPABLE_FAMILIES = {"llama3.1", "llama3.2", "qwen2.5", "mistral", "command-r", "deepseek-coder"}


def parse_model_info(raw_tag: Dict[str, Any]) -> ModelInfo:
    """Extract standard ModelInfo schema from an Ollama /api/tags entry."""
    details = raw_tag.get("details", {})
    return ModelInfo(
        id=raw_tag.get("name", "unknown"),
        name=raw_tag.get("name", "unknown"),
        provider="ollama",
        size_bytes=raw_tag.get("size"),
        parameter_size=details.get("parameter_size"),
        quantization=details.get("quantization_level"),
        family=details.get("family"),
        modified_at=raw_tag.get("modified_at"),
    )


def detect_capabilities(show_data: Dict[str, Any], model_name: str) -> ProviderCapabilities:
    """Analyze Ollama /api/show response to accurately report supported features."""
    details = show_data.get("details", {})
    model_info = show_data.get("model_info", {})
    template = show_data.get("template", "")

    family = (details.get("family") or "").lower()
    families = [f.lower() for f in details.get("families", [])]
    all_families = {family} | set(families)

    # Check tool support via family heuristics and template inspection
    has_tool_syntax = (
        ".Tools" in template
        or "[AVAILABLE_TOOLS]" in template
        or "<tools>" in template
        or any(tf in model_name.lower() for tf in ["llama3.1", "llama3.2", "qwen2.5", "mistral"])
        or bool(all_families.intersection(TOOL_CAPABLE_FAMILIES))
    )

    # Extract maximum context length if available
    context_length = None
    for key in ("context_length", f"{family}.context_length"):
        if key in model_info:
            try:
                context_length = int(model_info[key])
                break
            except (ValueError, TypeError):
                pass

    if context_length is None:
        # Sensible defaults based on modern architecture
        context_length = 8192 if ("llama" in family or "qwen" in family) else 4096

    return ProviderCapabilities(
        supports_chat=True,
        supports_generation=True,
        supports_streaming=True,
        supports_tools=has_tool_syntax,
        supports_structured_output=True,  # Ollama 0.1.30+ natively supports JSON format/schemas
        supports_system_prompt=True,
        max_context_length=context_length,
    )
