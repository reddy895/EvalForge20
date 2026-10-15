"""End-to-end unit and integration tests for the evaluation runner engine."""

import asyncio

import pytest
from app.datasets.validator import validate_dataset
from app.domain.models import EvaluatorConfiguration, TargetConfiguration, TargetType
from app.domain.state import EvaluationRunStatus
from app.providers.mock import MockProvider
from app.runner.config import EvaluationRunConfig
from app.runner.engine import EvaluationRunner


@pytest.mark.asyncio
async def test_runner_end_to_end_success():
    """Verify end-to-end evaluation run with mock provider and multiple metrics."""
    # 1. Load dataset
    report = validate_dataset("examples/datasets/basic.jsonl")
    assert report.is_valid
    cases = report.cases

    # 2. Setup mock provider with canned answers matching expected outputs
    canned = {
        "France": "Paris",
        "15 multiplied by 4": "60",
        "key 'status' equal to 'ok'": '{"status":"ok"}',
        "bloops": "Yes",
    }
    provider = MockProvider(
        canned_responses=canned,
        simulated_tokens={"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
    )

    # 3. Setup evaluation run config
    target_cfg = TargetConfiguration(
        target_name="mock-target",
        target_type=TargetType.MOCK,
        provider_name="mock",
        model_identifier="mock-model-v1",
    )
    evaluators = [
        EvaluatorConfiguration(evaluator_name="Exact Match", metric_id="exact_match"),
        EvaluatorConfiguration(evaluator_name="Normalized Match", metric_id="normalized_match"),
    ]

    completed_callbacks: list[str] = []

    async def on_case_done(case_res):
        completed_callbacks.append(case_res.case_id)

    config = EvaluationRunConfig(
        name="Basic E2E Run",
        target=target_cfg,
        evaluators=evaluators,
        max_concurrency=2,
    )

    runner = EvaluationRunner(config, on_case_completed=on_case_done)
    record, results, aggregates = await runner.run(cases, provider_instance=provider)

    assert record.status == EvaluationRunStatus.COMPLETED
    assert record.total_cases == 4
    assert record.completed_cases == 4
    assert record.failed_cases == 0

    assert len(results) == 4
    assert len(completed_callbacks) == 4

    assert aggregates.pass_rate == 1.0
    assert aggregates.metric_pass_rates["exact_match"] == 1.0
    assert aggregates.total_tokens == 60  # 4 * 15 tokens
    assert aggregates.mean_latency_ms is not None


@pytest.mark.asyncio
async def test_runner_partial_failures():
    """Verify partial results are preserved and run is marked completed_with_errors."""
    report = validate_dataset("examples/datasets/basic.jsonl")
    cases = report.cases

    # Fail specifically on France prompt
    provider = MockProvider(
        fail_on_prompts={"France": ConnectionRefusedError("Simulated provider disconnect")},
        default_response="generic response",
    )

    target_cfg = TargetConfiguration(target_name="mock-target", provider_name="mock")
    evaluators = [EvaluatorConfiguration(evaluator_name="Exact Match", metric_id="exact_match")]

    config = EvaluationRunConfig(target=target_cfg, evaluators=evaluators)
    runner = EvaluationRunner(config)
    record, results, aggregates = await runner.run(cases, provider_instance=provider)

    assert record.status == EvaluationRunStatus.COMPLETED_WITH_ERRORS
    assert record.completed_cases == 3
    assert record.failed_cases == 1
    assert aggregates.failed_cases == 1
    assert "provider_unavailable" in aggregates.error_distribution


@pytest.mark.asyncio
async def test_runner_cancellation():
    """Verify cancellation marks status as cancelled."""
    report = validate_dataset("examples/datasets/basic.jsonl")
    cases = report.cases

    provider = MockProvider(simulated_latency_ms=50.0)
    config = EvaluationRunConfig(
        target=TargetConfiguration(target_name="mock", provider_name="mock"),
        evaluators=[EvaluatorConfiguration(evaluator_name="Exact Match", metric_id="exact_match")],
        max_concurrency=1,
    )
    runner = EvaluationRunner(config)

    # Cancel runner shortly after launching
    async def cancel_soon():
        await asyncio.sleep(0.01)
        runner.cancel()

    asyncio.create_task(cancel_soon())
    record, results, _ = await runner.run(cases, provider_instance=provider)

    assert record.status == EvaluationRunStatus.CANCELLED
    cancelled_cases = [r for r in results if r.error_category == "cancelled"]
    assert len(cancelled_cases) > 0
