"""Versioned and timestamped pricing catalog sourced from official provider documentation."""

from typing import Any

from pydantic import BaseModel, Field


class PriceRule(BaseModel):
    """Verified pricing rule for a specific model or model family."""

    provider: str
    model_pattern: str
    display_name: str
    input_cost_per_m: float | None = Field(
        default=None, description="Input cost in USD per 1M tokens"
    )
    output_cost_per_m: float | None = Field(
        default=None, description="Output cost in USD per 1M tokens"
    )
    cached_input_cost_per_m: float | None = Field(
        default=None, description="Cached prompt input cost in USD per 1M tokens"
    )
    currency: str = Field(default="USD")
    unit: str = Field(default="per 1M tokens")
    source_url: str = Field(..., description="Official provider pricing reference URL")
    last_verified: str = Field(
        ..., description="ISO 8601 date when pricing was verified against official docs"
    )
    assumptions: str | None = Field(
        default=None, description="Tier or length constraints (e.g. prompts <= 128k)"
    )


# Official verified pricing catalog table
VERIFIED_PRICE_RULES: list[PriceRule] = [
    # --- OpenAI (https://developers.openai.com/api/docs/pricing) ---
    PriceRule(
        provider="openai",
        model_pattern="gpt-4o",
        display_name="GPT-4o",
        input_cost_per_m=2.50,
        output_cost_per_m=10.00,
        cached_input_cost_per_m=1.25,
        source_url="https://developers.openai.com/api/docs/pricing",
        last_verified="2025-01-15",
        assumptions="Standard tier pay-as-you-go",
    ),
    PriceRule(
        provider="openai",
        model_pattern="gpt-4o-mini",
        display_name="GPT-4o Mini",
        input_cost_per_m=0.15,
        output_cost_per_m=0.60,
        cached_input_cost_per_m=0.075,
        source_url="https://developers.openai.com/api/docs/pricing",
        last_verified="2025-01-15",
        assumptions="Standard tier pay-as-you-go",
    ),
    PriceRule(
        provider="openai",
        model_pattern="o1",
        display_name="o1",
        input_cost_per_m=15.00,
        output_cost_per_m=60.00,
        cached_input_cost_per_m=7.50,
        source_url="https://developers.openai.com/api/docs/pricing",
        last_verified="2024-12-17",
    ),
    PriceRule(
        provider="openai",
        model_pattern="o1-mini",
        display_name="o1-mini",
        input_cost_per_m=1.10,
        output_cost_per_m=4.40,
        cached_input_cost_per_m=0.55,
        source_url="https://developers.openai.com/api/docs/pricing",
        last_verified="2024-09-12",
    ),
    PriceRule(
        provider="openai",
        model_pattern="o3-mini",
        display_name="o3-mini",
        input_cost_per_m=1.10,
        output_cost_per_m=4.40,
        cached_input_cost_per_m=0.55,
        source_url="https://developers.openai.com/api/docs/pricing",
        last_verified="2025-01-31",
    ),
    PriceRule(
        provider="openai",
        model_pattern="gpt-4-turbo",
        display_name="GPT-4 Turbo",
        input_cost_per_m=10.00,
        output_cost_per_m=30.00,
        source_url="https://developers.openai.com/api/docs/pricing",
        last_verified="2024-04-09",
    ),
    PriceRule(
        provider="openai",
        model_pattern="gpt-3.5-turbo",
        display_name="GPT-3.5 Turbo",
        input_cost_per_m=0.50,
        output_cost_per_m=1.50,
        source_url="https://developers.openai.com/api/docs/pricing",
        last_verified="2024-02-01",
    ),
    # --- Anthropic Claude (https://docs.anthropic.com/) ---
    PriceRule(
        provider="anthropic",
        model_pattern="claude-3-5-sonnet-20241022",
        display_name="Claude 3.5 Sonnet (v2)",
        input_cost_per_m=3.00,
        output_cost_per_m=15.00,
        cached_input_cost_per_m=0.30,
        source_url="https://docs.anthropic.com/",
        last_verified="2024-11-01",
    ),
    PriceRule(
        provider="anthropic",
        model_pattern="claude-3-5-haiku-20241022",
        display_name="Claude 3.5 Haiku",
        input_cost_per_m=0.80,
        output_cost_per_m=4.00,
        cached_input_cost_per_m=0.08,
        source_url="https://docs.anthropic.com/",
        last_verified="2024-11-01",
    ),
    PriceRule(
        provider="anthropic",
        model_pattern="claude-3-opus-20240229",
        display_name="Claude 3 Opus",
        input_cost_per_m=15.00,
        output_cost_per_m=75.00,
        source_url="https://docs.anthropic.com/",
        last_verified="2024-03-01",
    ),
    # --- Google Gemini (https://ai.google.dev/gemini-api/docs) ---
    PriceRule(
        provider="gemini",
        model_pattern="gemini-1.5-pro",
        display_name="Gemini 1.5 Pro",
        input_cost_per_m=1.25,
        output_cost_per_m=5.00,
        cached_input_cost_per_m=0.3125,
        source_url="https://ai.google.dev/gemini-api/docs",
        last_verified="2024-10-01",
        assumptions="Prompts <= 128k tokens tier",
    ),
    PriceRule(
        provider="gemini",
        model_pattern="gemini-1.5-flash",
        display_name="Gemini 1.5 Flash",
        input_cost_per_m=0.075,
        output_cost_per_m=0.30,
        cached_input_cost_per_m=0.01875,
        source_url="https://ai.google.dev/gemini-api/docs",
        last_verified="2024-10-01",
    ),
    PriceRule(
        provider="gemini",
        model_pattern="gemini-2.0-flash",
        display_name="Gemini 2.0 Flash",
        input_cost_per_m=0.10,
        output_cost_per_m=0.40,
        source_url="https://ai.google.dev/gemini-api/docs",
        last_verified="2025-02-01",
    ),
    # --- Ollama Local Models ---
    PriceRule(
        provider="ollama",
        model_pattern="*",
        display_name="Ollama Local Inference",
        input_cost_per_m=0.0,
        output_cost_per_m=0.0,
        currency="USD",
        unit="local compute",
        source_url="https://ollama.com",
        last_verified="2025-01-01",
        assumptions="Zero cloud API charge. Local electricity and hardware amortization apply.",
    ),
]


class PricingCatalog:
    """Manages verified model price rules with lookup, custom overrides, and metadata."""

    def __init__(self, rules: list[PriceRule] | None = None):
        self._rules: list[PriceRule] = list(rules or VERIFIED_PRICE_RULES)
        self._custom_overrides: dict[str, PriceRule] = {}

    def get_rule(self, provider: str, model_identifier: str) -> PriceRule | None:
        """Find matching price rule by provider and exact or wildcard model identifier."""
        prov = provider.lower()
        model_id = model_identifier.lower()

        # Check explicit overrides first
        key = f"{prov}/{model_id}"
        if key in self._custom_overrides:
            return self._custom_overrides[key]

        # Check exact matches
        for rule in self._rules:
            if rule.provider.lower() == prov and rule.model_pattern.lower() == model_id:
                return rule

        # Check prefix or wildcard matches
        for rule in self._rules:
            if rule.provider.lower() == prov:
                pat = rule.model_pattern.lower()
                if pat == "*" or model_id.startswith(pat) or pat in model_id:
                    return rule

        return None

    def register_override(self, rule: PriceRule) -> None:
        """Register or update a custom pricing rule."""
        key = f"{rule.provider.lower()}/{rule.model_pattern.lower()}"
        self._custom_overrides[key] = rule

    def list_rules(self, provider: str | None = None) -> list[PriceRule]:
        """List all active pricing rules, optionally filtered by provider."""
        all_rules = list(self._custom_overrides.values()) + [
            r
            for r in self._rules
            if f"{r.provider.lower()}/{r.model_pattern.lower()}" not in self._custom_overrides
        ]
        if provider:
            prov = provider.lower()
            return [r for r in all_rules if r.provider.lower() == prov]
        return all_rules

    def to_dict_list(self) -> list[dict[str, Any]]:
        """Serialize catalog to list of dictionaries."""
        return [r.model_dump() for r in self.list_rules()]


# Global shared instance
pricing_catalog = PricingCatalog()
