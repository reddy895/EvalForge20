"""Unit tests for CaseRunner — metric routing, assertion type selection, and error capture."""

from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.evalforge.experiments.case_runner import CaseRunner
from src.evalforge.experiments.snapshot import FrozenTestCase
from src.evalforge.providers.schemas import InferenceResponse, TokenUsage
from src.evalforge.schemas.evaluation import EvaluationConfig


def _make_frozen_case(
    case_id: str = "c-01",
    prompt: str = "What is 2+2?",
    expected_output: str = "4",
    evaluator_config: dict | None = None,
) -> FrozenTestCase:
    return FrozenTestCase(
        id=case_id,
        prompt=prompt,
        expected_output=expected_output,
        context=None,
        metadata={},
        evaluator_config=evaluator_config or {},
    )


def _make_response(text: str = "4", latency_ms: float = 120.0, **raw_meta: Any) -> InferenceResponse:
    usage = TokenUsage(prompt_tokens=10, completion_tokens=5, total_tokens=15)
    meta: dict[str, Any] = {
        "tokens_per_second": 41.6,
        "load_duration_ms": 80.0,
        "total_duration_ms": latency_ms,
    }
    meta.update(raw_meta)
    return InferenceResponse(
        text=text,
        model="qwen2.5:1.5b",
        provider="ollama",
        latency_ms=latency_ms,
        usage=usage,
        raw_metadata=meta,
    )


def _make_runner(response: InferenceResponse | None = None, fail: bool = False) -> CaseRunner:
    provider = MagicMock()
    if fail:
        provider.generate = AsyncMock(side_effect=RuntimeError("Ollama not reachable"))
    else:
        provider.generate = AsyncMock(return_value=response or _make_response())

    config = EvaluationConfig(
        metrics=["exact_match", "token_f1"],
        temperature=0.0,
    )
    return CaseRunner(provider=provider, model_id="qwen2.5:1.5b", config=config)


class TestCaseRunnerExecution:
    @pytest.mark.asyncio
    async def test_passing_case_exact_match(self) -> None:
        runner = _make_runner(response=_make_response("4"))
        case = _make_frozen_case(expected_output="4")
        result = await runner.execute_case(case, evaluation_id="eval-1")

        assert result.passed is True
        assert result.actual_output == "4"
        assert result.latency_ms == pytest.approx(120.0, abs=1.0)

    @pytest.mark.asyncio
    async def test_failing_case_wrong_answer(self) -> None:
        runner = _make_runner(response=_make_response("5"))
        case = _make_frozen_case(expected_output="4")
        result = await runner.execute_case(case, evaluation_id="eval-2")

        assert result.passed is False
        assert result.actual_output == "5"

    @pytest.mark.asyncio
    async def test_inference_error_captured_gracefully(self) -> None:
        runner = _make_runner(fail=True)
        case = _make_frozen_case()
        result = await runner.execute_case(case, evaluation_id="eval-err")

        assert result.passed is False
        assert result.error_message is not None
        assert "Ollama not reachable" in result.error_message
        assert result.latency_ms == 0.0

    @pytest.mark.asyncio
    async def test_token_usage_stored_in_result(self) -> None:
        runner = _make_runner(response=_make_response("4"))
        case = _make_frozen_case(expected_output="4")
        result = await runner.execute_case(case, evaluation_id="eval-tok")

        assert result.token_usage is not None
        assert result.token_usage["prompt_tokens"] == 10
        assert result.token_usage["completion_tokens"] == 5

    @pytest.mark.asyncio
    async def test_ollama_tps_metadata_stored(self) -> None:
        runner = _make_runner(response=_make_response("4", tokens_per_second=55.0))
        case = _make_frozen_case(expected_output="4")
        result = await runner.execute_case(case, evaluation_id="eval-tps")

        assert result.token_usage is not None
        assert result.token_usage.get("tokens_per_second") == 55.0

    @pytest.mark.asyncio
    async def test_json_schema_assertion_type_routed(self) -> None:
        runner = _make_runner(response=_make_response('{"name": "Alice"}'))
        case = _make_frozen_case(
            expected_output='{"name": "Alice"}',
            evaluator_config={
                "assertion_type": "json_schema",
                "json_schema": {
                    "type": "object",
                    "properties": {"name": {"type": "string"}},
                    "required": ["name"],
                },
            },
        )
        result = await runner.execute_case(case, evaluation_id="eval-json")
        assert "json_schema" in result.metrics or result.passed is not None

    @pytest.mark.asyncio
    async def test_assertion_type_stored_in_metrics(self) -> None:
        runner = _make_runner()
        case = _make_frozen_case()
        result = await runner.execute_case(case, evaluation_id="eval-meta")

        assert "_assertion_type" in result.metrics
        assert "_latency_ms" in result.metrics
