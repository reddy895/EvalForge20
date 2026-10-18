"""Unit tests for pricing catalog, cost calculation, complexity bands, and task analysis."""

import httpx
import pytest
from app.domain.complexity import (
    ComplexityBand,
    aggregate_complexity_bands,
    classify_case_complexity,
)
from app.domain.models import EvaluationCase
from app.domain.results import AggregateMetrics, CaseResult
from app.pricing.calculator import CostCalculator
from app.pricing.pricing_catalog import PriceRule, PricingCatalog


def test_pricing_catalog_rules():
    catalog = PricingCatalog()

    # Exact rule lookup
    gpt4o_rule = catalog.get_rule("openai", "gpt-4o")
    assert gpt4o_rule is not None
    assert gpt4o_rule.input_cost_per_m == 2.50
    assert gpt4o_rule.output_cost_per_m == 10.00

    # Prefix/alias lookup
    sonnet_rule = catalog.get_rule("anthropic", "claude-3-5-sonnet-20241022")
    assert sonnet_rule is not None
    assert sonnet_rule.input_cost_per_m == 3.00

    # Ollama wildcard lookup
    ollama_rule = catalog.get_rule("ollama", "llama3.1:8b")
    assert ollama_rule is not None
    assert ollama_rule.input_cost_per_m == 0.0

    # Custom override
    custom_rule = PriceRule(
        provider="custom",
        model_pattern="my-model",
        display_name="My Model",
        input_cost_per_m=0.5,
        output_cost_per_m=1.0,
        source_url="https://example.com/pricing",
        last_verified="2025-01-01",
    )
    catalog.register_override(custom_rule)
    retrieved = catalog.get_rule("custom", "my-model")
    assert retrieved is not None
    assert retrieved.input_cost_per_m == 0.5


def test_cost_calculator_cloud_model():
    calculator = CostCalculator()
    case_res = CaseResult(
        case_id="c1",
        run_id="r1",
        input="test",
        actual_output="ans",
        latency_ms=250.0,
        token_usage={"prompt_tokens": 1000, "completion_tokens": 500, "total_tokens": 1500},
    )

    # gpt-4o: $2.50 / 1M in, $10.00 / 1M out
    # 1000 in = 0.0025, 500 out = 0.005 -> total = 0.0075
    breakdown = calculator.calculate_case_cost(
        case_res, provider="openai", model_identifier="gpt-4o"
    )
    assert breakdown.is_cost_known is True
    assert breakdown.cloud_cost_usd == pytest.approx(0.0075, rel=1e-3)
    assert breakdown.total_estimated_cost_usd == pytest.approx(0.0075, rel=1e-3)


def test_cost_calculator_ollama_local():
    calculator = CostCalculator()
    case_res = CaseResult(
        case_id="c2",
        run_id="r1",
        input="local test",
        actual_output="ans",
        latency_ms=3600.0,  # 3.6 seconds
        token_usage={"prompt_tokens": 50, "completion_tokens": 50},
    )

    breakdown = calculator.calculate_case_cost(
        case_res, provider="ollama", model_identifier="llama3.1:8b", local_cost_per_hour=0.15
    )
    assert breakdown.is_cost_known is True
    assert breakdown.cloud_cost_usd == 0.0
    assert breakdown.local_hardware_cost_usd is not None
    assert breakdown.local_hardware_cost_usd > 0.0


def test_cost_calculator_run_aggregation():
    calculator = CostCalculator()
    results = [
        CaseResult(
            case_id="c1",
            run_id="r1",
            input="p1",
            actual_output="a1",
            token_usage={"prompt_tokens": 1000, "completion_tokens": 1000},
        ),
        CaseResult(
            case_id="c2",
            run_id="r1",
            input="p2",
            actual_output="a2",
            token_usage={"prompt_tokens": 1000, "completion_tokens": 1000},
        ),
    ]
    aggregates = AggregateMetrics(
        total_cases=2,
        completed_cases=2,
        failed_cases=0,
        pass_rate=1.0,
    )

    run_cost = calculator.calculate_run_cost(
        results=results,
        aggregates=aggregates,
        provider="openai",
        model_identifier="gpt-4o-mini",
    )
    assert run_cost.is_cost_known is True
    assert run_cost.total_tokens == 4000
    assert run_cost.cost_per_successful_case_usd is not None
    assert run_cost.cost_per_1k_tasks_usd is not None


def test_complexity_classification_and_aggregation():
    # 1. Explicit metadata
    low_case = EvaluationCase(id="l1", input="simple", metadata={"complexity": "low"})
    assert classify_case_complexity(low_case) == ComplexityBand.LOW

    high_case = EvaluationCase(id="h1", input="complex", metadata={"complexity": "high"})
    assert classify_case_complexity(high_case) == ComplexityBand.HIGH

    # 2. Heuristic
    tool_case = EvaluationCase(id="t1", input="use tool", tools=[{"name": "calculator"}])
    assert classify_case_complexity(tool_case) == ComplexityBand.HIGH

    # 3. Insufficient data threshold (< 3 cases)
    results = [
        CaseResult(case_id="l1", run_id="r1", input="simple", actual_output="ok"),
        CaseResult(case_id="l2", run_id="r1", input="simple 2", actual_output="ok"),
    ]
    cases_map = {
        "l1": EvaluationCase(id="l1", input="simple", metadata={"complexity": "low"}),
        "l2": EvaluationCase(id="l2", input="simple 2", metadata={"complexity": "low"}),
    }
    bands = aggregate_complexity_bands(results, cases_map=cases_map)
    assert bands["low"].total_cases == 2
    assert bands["low"].has_sufficient_data is False
    assert "Insufficient data" in (bands["low"].insufficient_data_note or "")

    # 4. Sufficient data threshold (>= 3 cases)
    results.append(CaseResult(case_id="l3", run_id="r1", input="simple 3", actual_output="ok"))
    cases_map["l3"] = EvaluationCase(id="l3", input="simple 3", metadata={"complexity": "low"})
    bands2 = aggregate_complexity_bands(results, cases_map=cases_map)
    assert bands2["low"].total_cases == 3
    assert bands2["low"].has_sufficient_data is True
    assert bands2["low"].insufficient_data_note is None


@pytest.mark.asyncio
async def test_pricing_and_estimate_api():
    from app.main import app

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://testserver"
    ) as client:
        # GET /v1/pricing/rules
        resp = await client.get("/v1/pricing/rules?provider=openai")
        assert resp.status_code == 200
        rules = resp.json()
        assert len(rules) >= 2
        assert any(r["model_pattern"] == "gpt-4o" for r in rules)

        # POST /v1/pricing/estimate
        est_resp = await client.post(
            "/v1/pricing/estimate",
            json={
                "provider": "openai",
                "model_identifier": "gpt-4o",
                "prompt_tokens": 10000,
                "completion_tokens": 5000,
                "num_tasks": 10,
            },
        )
        assert est_resp.status_code == 200
        data = est_resp.json()
        assert data["is_cost_known"] is True
        assert data["cloud_cost_usd"] > 0.0
        assert data["cost_per_1k_tasks_usd"] > 0.0
