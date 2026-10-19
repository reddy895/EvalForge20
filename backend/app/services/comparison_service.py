"""Multi-model comparison service generating side-by-side matrices across 2 to 4 models."""

from backend.app.schemas.comparisons import (
    ComparisonRow,
    ModelComparisonRequest,
    ModelComparisonResult,
)
from backend.app.services.model_catalog import ModelCatalogService


class ComparisonService:
    """Computes comparative matrices across model capabilities, benchmarks, and costs."""

    def __init__(self, catalog_service: ModelCatalogService | None = None):
        self.catalog = catalog_service or ModelCatalogService()

    async def compare_models(self, req: ModelComparisonRequest) -> ModelComparisonResult:
        """Generate side-by-side comparison across requested model IDs."""
        profiles = []
        for mid in req.model_ids:
            p = await self.catalog.get_model_profile(mid)
            if p:
                profiles.append(p)

        if len(profiles) < 2:
            return ModelComparisonResult(
                compared_models=[],
                matrix=[],
                summary_verdict="At least 2 valid models required for side-by-side comparison.",
            )

        compared_models = [{"id": p.id, "name": p.name, "provider": p.provider} for p in profiles]

        # 1. Architecture & Parameters
        param_vals = {p.id: p.parameter_count or "Unknown" for p in profiles}
        context_vals = {p.id: f"{p.context_window:,} tokens" for p in profiles}
        modalities_vals = {p.id: ", ".join(p.modalities) for p in profiles}

        # 2. Local Execution & Requirements
        local_vals = {
            p.id: "Yes (Ollama / Local)" if p.is_local else "No (Cloud API)" for p in profiles
        }
        ram_vals = {
            p.id: f"{p.hardware.min_ram_gb} GB RAM" if p.is_local else "0 GB (Hosted)"
            for p in profiles
        }

        # 3. Tool Use & Structured Output
        tools_vals = {p.id: "Supported" if p.supports_tools else "Not Verified" for p in profiles}
        json_vals = {
            p.id: "Supported" if p.supports_structured_output else "Not Verified" for p in profiles
        }

        # 4. Pricing / Cost
        price_vals = {}
        for p in profiles:
            if p.is_local:
                price_vals[p.id] = "Free ($0.00 / Local Compute)"
            elif p.pricing and p.pricing.input_cost_per_m:
                price_vals[p.id] = (
                    f"${p.pricing.input_cost_per_m:.2f} in / ${p.pricing.output_cost_per_m:.2f} out per 1M"
                )
            else:
                price_vals[p.id] = "Cloud Tier"

        # 5. Benchmarks
        humaneval_vals = {}
        gsm8k_vals = {}
        mmlu_vals = {}
        for p in profiles:
            h_score = next(
                (b.score for b in p.benchmarks if "humaneval" in b.benchmark_name.lower()), None
            )
            g_score = next(
                (b.score for b in p.benchmarks if "gsm8k" in b.benchmark_name.lower()), None
            )
            m_score = next(
                (b.score for b in p.benchmarks if "mmlu" in b.benchmark_name.lower()), None
            )
            humaneval_vals[p.id] = f"{h_score:.1f}%" if h_score is not None else "—"
            gsm8k_vals[p.id] = f"{g_score:.1f}%" if g_score is not None else "—"
            mmlu_vals[p.id] = f"{m_score:.1f}%" if m_score is not None else "—"

        rows = [
            ComparisonRow(
                metric_name="Execution Environment", category="Deployment", values=local_vals
            ),
            ComparisonRow(
                metric_name="Minimum System Memory", category="Hardware", values=ram_vals
            ),
            ComparisonRow(
                metric_name="Context Window", category="Architecture", values=context_vals
            ),
            ComparisonRow(metric_name="Parameter Size", category="Architecture", values=param_vals),
            ComparisonRow(
                metric_name="Input / Output Modalities",
                category="Architecture",
                values=modalities_vals,
            ),
            ComparisonRow(
                metric_name="Tool Calling Support", category="Capabilities", values=tools_vals
            ),
            ComparisonRow(
                metric_name="Structured JSON Support", category="Capabilities", values=json_vals
            ),
            ComparisonRow(
                metric_name="HumanEval (Coding Pass@1)",
                category="Benchmarks",
                values=humaneval_vals,
                note="Published technical reports",
            ),
            ComparisonRow(
                metric_name="GSM8K (Math Accuracy)",
                category="Benchmarks",
                values=gsm8k_vals,
                note="Published technical reports",
            ),
            ComparisonRow(
                metric_name="MMLU (General Knowledge)",
                category="Benchmarks",
                values=mmlu_vals,
                note="Published technical reports",
            ),
            ComparisonRow(metric_name="Pricing / Cost", category="Economics", values=price_vals),
        ]

        # Formulate intelligent summary verdict
        best_code = max(
            profiles,
            key=lambda p: next(
                (b.score for b in p.benchmarks if "humaneval" in b.benchmark_name.lower()), 0
            ),
        )
        local_models = [p for p in profiles if p.is_local]

        verdict = (
            f"For coding accuracy, {best_code.name} demonstrates the strongest benchmark evidence. "
        )
        if local_models:
            verdict += f"For zero-cost offline privacy, {local_models[0].name} runs directly on local hardware without cloud API dependencies."

        notes = [
            "Benchmarks are gathered from official published technical reports under standard greedy/temperature=0 evaluation.",
            "Local memory estimates reflect 4-bit quantized GGUF execution via Ollama.",
        ]

        return ModelComparisonResult(
            compared_models=compared_models,
            matrix=rows,
            summary_verdict=verdict,
            comparability_notes=notes,
        )
