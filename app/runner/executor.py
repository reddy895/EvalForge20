import json

from app.domain.contracts import (
    EvaluatorContract,
    EvaluatorInput,
    ProviderRequest,
    ProviderResponse,
)
from app.domain.models import EvaluationCase, EvaluatorConfiguration, TargetConfiguration
from app.domain.results import CaseResult, MetricResult
from app.providers.base import BaseProvider
from app.runner.retry import execute_with_retry


async def execute_case(
    case: EvaluationCase,
    provider: BaseProvider,
    target_config: TargetConfiguration,
    evaluator_configs: list[EvaluatorConfiguration],
    evaluators_map: dict[str, EvaluatorContract],
    run_id: str,
    max_retries: int = 2,
) -> CaseResult:
    """Execute a single test case against the target provider and evaluate its outputs."""
    # 1. Format provider prompt
    if isinstance(case.input, str):
        prompt_text = case.input
    else:
        prompt_text = json.dumps(case.input, ensure_ascii=False)

    request = ProviderRequest(
        prompt=prompt_text,
        temperature=target_config.temperature,
        max_tokens=target_config.max_tokens,
        tools=case.tools,
        response_format=case.metadata.get("response_format"),
        extra_params=target_config.extra_params,
    )

    # 2. Invoke provider with bounded retry for transient errors
    async def _call() -> ProviderResponse:
        return await provider.generate(request)

    resp = await execute_with_retry(_call, max_retries=max_retries)

    # 3. Handle provider-level failures
    trace_info = {
        "provider": target_config.provider_name,
        "model": target_config.model_identifier,
        "temperature": target_config.temperature,
        "max_tokens": target_config.max_tokens,
    }

    if not resp.is_success or resp.output_text is None:
        return CaseResult(
            case_id=case.id,
            run_id=run_id,
            input=case.input,
            actual_output=None,
            expected_output=case.expected_output,
            metrics=[],
            latency_ms=resp.latency_ms,
            token_usage=resp.token_usage,
            error_category=resp.error_category or "provider_error",
            error_message=resp.error_message or "Provider failed to produce output",
            trace=trace_info,
        )

    # 4. Run configured evaluators on output
    metric_results: list[MetricResult] = []
    for eval_cfg in evaluator_configs:
        evaluator = evaluators_map.get(eval_cfg.metric_id)
        if evaluator is None:
            continue

        eval_input = EvaluatorInput(
            case=case,
            actual_output=resp.output_text,
            options=eval_cfg.options,
        )
        try:
            m_res = await evaluator.evaluate(eval_input)
            metric_results.append(m_res)
        except Exception as exc:
            metric_results.append(
                MetricResult(
                    metric_id=eval_cfg.metric_id,
                    metric_name=evaluator.metric_name,
                    score=None,
                    passed=False,
                    reason=f"Evaluator execution exception: {exc}",
                    details={"error": str(exc)},
                    is_model_based=False,
                )
            )

    return CaseResult(
        case_id=case.id,
        run_id=run_id,
        input=case.input,
        actual_output=resp.output_text,
        expected_output=case.expected_output,
        metrics=metric_results,
        latency_ms=resp.latency_ms,
        token_usage=resp.token_usage,
        error_category=None,
        error_message=None,
        trace=trace_info,
    )
