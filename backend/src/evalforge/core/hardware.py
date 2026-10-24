"""Hardware sizing and memory requirement calculator for local LLM inference."""

from dataclasses import dataclass
from typing import Any, Literal

QuantizationType = Literal["Q4_K_M", "Q5_K_M", "Q8_0", "FP16"]

@dataclass
class HardwareEstimate:
    parameter_billions: float
    quantization: QuantizationType
    weights_ram_gb: float
    context_overhead_gb: float
    recommended_min_ram_gb: float
    fits_in_8gb: bool
    fits_in_16gb: bool
    fits_in_32gb: bool
    warning: str | None = None

class HardwareConstraintAnalyzer:
    """Calculates realistic RAM/VRAM requirements based on model weight parameters and quantization."""

    BITS_PER_WEIGHT: dict[QuantizationType, float] = {
        "Q4_K_M": 4.5,
        "Q5_K_M": 5.5,
        "Q8_0": 8.5,
        "FP16": 16.0,
    }

    @classmethod
    def estimate_ram(
        cls,
        parameters_b: float,
        quantization: QuantizationType = "Q4_K_M",
        context_length: int = 8192,
    ) -> HardwareEstimate:
        bits = cls.BITS_PER_WEIGHT.get(quantization, 4.5)
        # Weight memory in GB (1B params * bits / 8 / 10^9)
        weights_gb = round((parameters_b * 1e9 * bits) / (8 * (1024**3)), 2)
        # KV cache overhead approximation (2 * layers * heads * dim * context)
        # Heuristic: ~0.5 GB per 8k context for 7B, scales with parameter size
        kv_overhead_gb = round((context_length / 8192) * (parameters_b / 7.0) * 0.75, 2)
        # Total minimum recommended (weights + KV cache + 2GB OS/runtime buffer)
        total_rec = round(weights_gb + kv_overhead_gb + 2.0, 1)

        fits_8 = total_rec <= 8.0
        fits_16 = total_rec <= 16.0
        fits_32 = total_rec <= 32.0

        warning = None
        if total_rec > 32.0:
            warning = f"Model requires ~{total_rec}GB RAM. Ensure workstation has at least 64GB RAM or high-VRAM GPU."
        elif total_rec > 16.0:
            warning = f"Model requires ~{total_rec}GB RAM. Will exceed standard 16GB laptops."

        return HardwareEstimate(
            parameter_billions=parameters_b,
            quantization=quantization,
            weights_ram_gb=weights_gb,
            context_overhead_gb=kv_overhead_gb,
            recommended_min_ram_gb=total_rec,
            fits_in_8gb=fits_8,
            fits_in_16gb=fits_16,
            fits_in_32gb=fits_32,
            warning=warning,
        )

    @classmethod
    def analyze_context_scaling(
        cls,
        parameters_b: float,
        quantization: QuantizationType = "Q4_K_M",
        context_steps: list[int] | None = None,
    ) -> list[dict[str, Any]]:
        """Project memory growth across varying context window sizes."""
        steps = context_steps or [2048, 4096, 8192, 16384, 32768]
        return [
            {
                "context_length": ctx,
                "weights_ram_gb": cls.estimate_ram(parameters_b, quantization, ctx).weights_ram_gb,
                "context_overhead_gb": cls.estimate_ram(parameters_b, quantization, ctx).context_overhead_gb,
                "recommended_min_ram_gb": cls.estimate_ram(parameters_b, quantization, ctx).recommended_min_ram_gb,
            }
            for ctx in steps
        ]

