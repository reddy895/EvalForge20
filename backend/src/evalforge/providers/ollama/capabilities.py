"""Model capability detection and metadata parser for Ollama."""

from typing import Any

from src.evalforge.providers.schemas import HardwareRequirements, ModelInfo, ProviderCapabilities

# Known families with robust native tool-calling template support in Ollama
TOOL_CAPABLE_FAMILIES = {
    "llama3.1",
    "llama3.2",
    "qwen2",
    "qwen2.5",
    "mistral",
    "command-r",
    "deepseek-coder",
}


def parse_model_info(raw_tag: dict[str, Any]) -> ModelInfo:
    """Extract standard ModelInfo schema from an Ollama /api/tags entry."""
    details = raw_tag.get("details", {})
    name = raw_tag.get("name", "unknown")
    caps = raw_tag.get("capabilities", [])
    is_remote = bool(raw_tag.get("remote_model") or raw_tag.get("remote_host") or ":cloud" in name)

    size_bytes = raw_tag.get("size")
    param_size = details.get("parameter_size") or ""
    quant = details.get("quantization_level") or ("Cloud" if is_remote else "Unknown")
    family = details.get("family") or ""
    ctx_len = details.get("context_length") or 4096
    disk_gb = round(size_bytes / 1e9, 2) if size_bytes else 4.0

    supports_tools = "tools" in caps or family in TOOL_CAPABLE_FAMILIES or "qwen" in family or "llama" in family

    # Compute sensible RAM requirements based on parameter count
    min_ram = 4.0
    rec_ram = 8.0
    param_lower = param_size.lower()
    if "1." in param_lower or "1b" in param_lower:
        min_ram = 2.0
        rec_ram = 4.0
    elif "3b" in param_lower:
        min_ram = 4.0
        rec_ram = 8.0
    elif "7b" in param_lower or "8b" in param_lower:
        min_ram = 8.0
        rec_ram = 16.0
    elif "14b" in param_lower:
        min_ram = 16.0
        rec_ram = 32.0
    elif "70b" in param_lower:
        min_ram = 48.0
        rec_ram = 64.0

    return ModelInfo(
        id=name,
        name=name,
        provider="ollama",
        model_identifier=name,
        size_bytes=size_bytes,
        parameter_size=param_size,
        parameter_count=param_size,
        quantization=quant,
        family=family,
        context_window=ctx_len,
        supports_tools=supports_tools,
        supports_structured_output=True,
        is_local=not is_remote,
        is_installed=not is_remote,
        is_remote=is_remote,
        description=f"Local Ollama model {name} ({param_size}, {quant}).",
        hardware=HardwareRequirements(
            min_ram_gb=min_ram,
            recommended_ram_gb=rec_ram,
            quantization=quant,
            context_length=ctx_len,
            disk_space_gb=disk_gb,
        ),
        modified_at=raw_tag.get("modified_at"),
    )


def detect_capabilities(show_data: dict[str, Any], model_name: str) -> ProviderCapabilities:
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
