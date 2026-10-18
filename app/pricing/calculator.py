"""Cost calculation and estimation engine based on measured token usage and pricing rules."""

from pydantic import BaseModel, Field

from app.domain.results import AggregateMetrics, CaseResult
from app.pricing.pricing_catalog import PriceRule, pricing_catalog


class CostBreakdown(BaseModel):
    """Detailed cost breakdown for a test case or an evaluation run."""

    prompt_tokens: int | None = Field(default=None, description="Measured prompt tokens")
    completion_tokens: int | None = Field(default=None, description="Measured completion tokens")
    total_tokens: int | None = Field(default=None, description="Total tokens consumed")
    cloud_cost_usd: float | None = Field(
        default=None, description="Calculated API cost for hosted providers"
    )
    local_hardware_cost_usd: float | None = Field(
        default=None, description="Estimated local hardware/electricity cost if configured"
    )
    total_estimated_cost_usd: float | None = Field(default=None, description="Total estimated cost")
    cost_per_successful_case_usd: float | None = Field(
        default=None, description="Cost per passing evaluation case"
    )
    cost_per_1k_tasks_usd: float | None = Field(
        default=None, description="Projected cost per 1,000 tasks"
    )
    is_cost_known: bool = Field(
        default=False, description="True if pricing rules and token measurements exist"
    )
    pricing_source: str | None = Field(default=None, description="Source URL or catalog reference")
    assumptions: str | None = Field(
        default=None, description="Documented assumptions used for calculation"
    )


class CostCalculator:
    """Calculates real costs and projections from measured usage."""

    def __init__(self, catalog=None):
        self.catalog = catalog or pricing_catalog

    def calculate_case_cost(
        self,
        result: CaseResult,
        provider: str,
        model_identifier: str,
        local_cost_per_hour: float = 0.15,
    ) -> CostBreakdown:
        """Calculate estimated cost for an individual test case."""
        rule: PriceRule | None = self.catalog.get_rule(provider, model_identifier)

        usage = result.token_usage or {}
        p_tokens = usage.get("prompt_tokens")
        c_tokens = usage.get("completion_tokens")
        tot_tokens = usage.get("total_tokens") or (
            (p_tokens or 0) + (c_tokens or 0)
            if (p_tokens is not None or c_tokens is not None)
            else None
        )

        # 1. Local Ollama cost estimation
        if provider.lower() == "ollama":
            # Zero cloud API fee
            latency_sec = (result.latency_ms or 0.0) / 1000.0
            local_cost = round((latency_sec / 3600.0) * local_cost_per_hour, 6)
            return CostBreakdown(
                prompt_tokens=p_tokens,
                completion_tokens=c_tokens,
                total_tokens=tot_tokens,
                cloud_cost_usd=0.0,
                local_hardware_cost_usd=local_cost,
                total_estimated_cost_usd=local_cost,
                is_cost_known=True,
                pricing_source="https://ollama.com",
                assumptions=f"Zero API fee. Hardware/power estimated at ${local_cost_per_hour:.2f}/hour.",
            )

        # 2. Cloud provider pricing
        if rule is None or rule.input_cost_per_m is None or rule.output_cost_per_m is None:
            return CostBreakdown(
                prompt_tokens=p_tokens,
                completion_tokens=c_tokens,
                total_tokens=tot_tokens,
                cloud_cost_usd=None,
                total_estimated_cost_usd=None,
                is_cost_known=False,
                pricing_source=rule.source_url if rule else None,
                assumptions="Pricing metadata unavailable for this provider/model.",
            )

        if p_tokens is None or c_tokens is None:
            return CostBreakdown(
                prompt_tokens=p_tokens,
                completion_tokens=c_tokens,
                total_tokens=tot_tokens,
                cloud_cost_usd=None,
                total_estimated_cost_usd=None,
                is_cost_known=False,
                pricing_source=rule.source_url,
                assumptions="Token usage was not returned by provider.",
            )

        in_cost = (p_tokens / 1_000_000.0) * rule.input_cost_per_m
        out_cost = (c_tokens / 1_000_000.0) * rule.output_cost_per_m
        total_cost = round(in_cost + out_cost, 6)

        return CostBreakdown(
            prompt_tokens=p_tokens,
            completion_tokens=c_tokens,
            total_tokens=tot_tokens,
            cloud_cost_usd=total_cost,
            total_estimated_cost_usd=total_cost,
            is_cost_known=True,
            pricing_source=rule.source_url,
            assumptions=rule.assumptions or "Standard pay-as-you-go per 1M tokens",
        )

    def calculate_run_cost(
        self,
        results: list[CaseResult],
        aggregates: AggregateMetrics,
        provider: str,
        model_identifier: str,
        local_cost_per_hour: float = 0.15,
    ) -> CostBreakdown:
        """Calculate aggregate cost and projections for an entire evaluation run."""
        if not results:
            return CostBreakdown(is_cost_known=False)

        case_breakdowns = [
            self.calculate_case_cost(
                r, provider, model_identifier, local_cost_per_hour=local_cost_per_hour
            )
            for r in results
        ]

        total_p_tokens = sum(
            b.prompt_tokens for b in case_breakdowns if b.prompt_tokens is not None
        )
        total_c_tokens = sum(
            b.completion_tokens for b in case_breakdowns if b.completion_tokens is not None
        )
        total_toks = (
            (total_p_tokens + total_c_tokens) if (total_p_tokens or total_c_tokens) else None
        )

        all_known = all(b.is_cost_known for b in case_breakdowns)
        if not all_known:
            rule = self.catalog.get_rule(provider, model_identifier)
            return CostBreakdown(
                prompt_tokens=total_p_tokens,
                completion_tokens=total_c_tokens,
                total_tokens=total_toks,
                cloud_cost_usd=None,
                total_estimated_cost_usd=None,
                is_cost_known=False,
                pricing_source=rule.source_url if rule else None,
                assumptions="Incomplete token measurements or unconfigured model pricing.",
            )

        tot_cloud = sum(b.cloud_cost_usd or 0.0 for b in case_breakdowns)
        tot_local = sum(b.local_hardware_cost_usd or 0.0 for b in case_breakdowns)
        total_cost = round(tot_cloud + tot_local, 6)

        # Cost per successful case
        pass_count = aggregates.completed_cases
        cost_per_success = round(total_cost / pass_count, 6) if pass_count > 0 else None

        # Cost per 1,000 tasks
        total_cases = len(results)
        cost_per_1k = round((total_cost / total_cases) * 1000.0, 4) if total_cases > 0 else None

        first_rule = self.catalog.get_rule(provider, model_identifier)

        return CostBreakdown(
            prompt_tokens=total_p_tokens,
            completion_tokens=total_c_tokens,
            total_tokens=total_toks,
            cloud_cost_usd=round(tot_cloud, 6),
            local_hardware_cost_usd=round(tot_local, 6) if tot_local > 0 else None,
            total_estimated_cost_usd=total_cost,
            cost_per_successful_case_usd=cost_per_success,
            cost_per_1k_tasks_usd=cost_per_1k,
            is_cost_known=True,
            pricing_source=first_rule.source_url if first_rule else None,
            assumptions=first_rule.assumptions if first_rule else None,
        )


cost_calculator = CostCalculator()
