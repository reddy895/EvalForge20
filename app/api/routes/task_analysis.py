"""Task capability, complexity analysis, and pricing estimation API endpoints."""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.application.evaluation_service import EvaluationService
from app.domain.complexity import TaskCategoryMetrics
from app.pricing.calculator import CostBreakdown, cost_calculator
from app.pricing.pricing_catalog import PriceRule, pricing_catalog
from app.storage.database import get_db

analysis_router = APIRouter(prefix="/v1", tags=["Task Analysis & Pricing"])


class CostEstimateRequest(BaseModel):
    """Payload to estimate model execution cost for given token counts."""

    provider: str
    model_identifier: str
    prompt_tokens: int = Field(default=1000, ge=0)
    completion_tokens: int = Field(default=500, ge=0)
    num_tasks: int = Field(default=1, ge=1)


class RunAnalysisResponse(BaseModel):
    """Comprehensive task capability, complexity tier, and cost analysis for an evaluation run."""

    run_id: str
    model_identifier: str
    provider_name: str
    total_cases: int
    pass_rate: float | None
    complexity_bands: dict[str, Any]
    task_categories: list[TaskCategoryMetrics]
    cost_breakdown: CostBreakdown


@analysis_router.get(
    "/analysis/tasks/{run_id}",
    response_model=RunAnalysisResponse,
    summary="Get task capability and complexity analysis for a run",
)
@analysis_router.get(
    "/task-analysis/{run_id}",
    response_model=RunAnalysisResponse,
    summary="Get task capability and complexity analysis for a run (alias)",
)
async def get_run_task_analysis(
    run_id: str,
    db: Session = Depends(get_db),
) -> RunAnalysisResponse:
    """Retrieve structured strengths/weaknesses by task category, complexity bands, and costs."""
    service = EvaluationService(db)
    record = service.get_run(run_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Evaluation run '{run_id}' not found",
        )

    case_results = service.get_run_results(run_id)
    aggregates = service.get_run_aggregates(run_id)
    if not aggregates:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Run '{run_id}' has no aggregate metrics computed",
        )

    # 1. Complexity bands
    complexity_bands = aggregates.complexity_performance or {}

    # 2. Task categories
    cat_metrics: list[TaskCategoryMetrics] = []
    # Group cases by category
    cats_map: dict[str, list[Any]] = {}
    for c in case_results:
        cat = c.trace.get("category") if c.trace else None
        if not cat:
            cat = "general"
        cats_map.setdefault(cat, []).append(c)

    for cat_name, cases in cats_map.items():
        tot = len(cases)
        passed = sum(1 for c in cases if c.passed)
        failed = tot - passed
        p_rate = round(passed / tot, 4) if tot > 0 else None
        f_rate = round(failed / tot, 4) if tot > 0 else None
        lats = [c.latency_ms for c in cases if c.latency_ms is not None and c.latency_ms > 0]
        mean_lat = round(sum(lats) / len(lats), 2) if lats else None

        rep_failures = [
            {
                "case_id": c.case_id,
                "input": str(c.input)[:150],
                "error_message": c.error_message or "Assertion check failed",
                "actual_output": str(c.actual_output)[:150] if c.actual_output else None,
            }
            for c in cases
            if not c.passed
        ][:3]

        cat_metrics.append(
            TaskCategoryMetrics(
                category=cat_name,
                total_cases=tot,
                passed_cases=passed,
                failed_cases=failed,
                pass_rate=p_rate,
                failure_rate=f_rate,
                mean_latency_ms=mean_lat,
                representative_failures=rep_failures,
            )
        )

    # 3. Cost calculation
    cost = cost_calculator.calculate_run_cost(
        results=case_results,
        aggregates=aggregates,
        provider=record.config.target.provider_name,
        model_identifier=record.config.target.model_identifier,
    )

    return RunAnalysisResponse(
        run_id=run_id,
        model_identifier=record.config.target.model_identifier,
        provider_name=record.config.target.provider_name,
        total_cases=record.total_cases,
        pass_rate=aggregates.pass_rate,
        complexity_bands=complexity_bands,
        task_categories=cat_metrics,
        cost_breakdown=cost,
    )


@analysis_router.get(
    "/pricing/rules",
    response_model=list[PriceRule],
    summary="List all verified pricing rules",
)
async def list_pricing_rules(
    provider: str | None = Query(default=None, description="Filter by provider"),
) -> list[PriceRule]:
    """Retrieve timestamped token pricing rules sourced from official provider documentation."""
    return pricing_catalog.list_rules(provider=provider)


@analysis_router.post(
    "/pricing/rules",
    response_model=PriceRule,
    summary="Register custom pricing rule",
)
async def register_pricing_rule(rule: PriceRule) -> PriceRule:
    """Override or configure custom token pricing for a provider and model pattern."""
    pricing_catalog.register_override(rule)
    return rule


@analysis_router.post(
    "/pricing/estimate",
    response_model=CostBreakdown,
    summary="Estimate cost for token counts",
)
async def estimate_cost(req: CostEstimateRequest) -> CostBreakdown:
    """Project API and local compute cost for arbitrary token quantities."""
    rule = pricing_catalog.get_rule(req.provider, req.model_identifier)

    tot_p = req.prompt_tokens * req.num_tasks
    tot_c = req.completion_tokens * req.num_tasks
    total_tokens = tot_p + tot_c

    if req.provider.lower() == "ollama":
        return CostBreakdown(
            prompt_tokens=tot_p,
            completion_tokens=tot_c,
            total_tokens=total_tokens,
            cloud_cost_usd=0.0,
            total_estimated_cost_usd=0.0,
            cost_per_1k_tasks_usd=0.0,
            is_cost_known=True,
            pricing_source="https://ollama.com",
            assumptions="Local inference has zero cloud API charge.",
        )

    if rule is None or rule.input_cost_per_m is None or rule.output_cost_per_m is None:
        return CostBreakdown(
            prompt_tokens=tot_p,
            completion_tokens=tot_c,
            total_tokens=total_tokens,
            is_cost_known=False,
            pricing_source=rule.source_url if rule else None,
            assumptions="Pricing metadata unavailable for this model.",
        )

    in_cost = (tot_p / 1_000_000.0) * rule.input_cost_per_m
    out_cost = (tot_c / 1_000_000.0) * rule.output_cost_per_m
    total_cost = round(in_cost + out_cost, 6)
    per_1k = round((total_cost / req.num_tasks) * 1000.0, 4)

    return CostBreakdown(
        prompt_tokens=tot_p,
        completion_tokens=tot_c,
        total_tokens=total_tokens,
        cloud_cost_usd=total_cost,
        total_estimated_cost_usd=total_cost,
        cost_per_1k_tasks_usd=per_1k,
        is_cost_known=True,
        pricing_source=rule.source_url,
        assumptions=rule.assumptions or "Standard tier pricing",
    )
