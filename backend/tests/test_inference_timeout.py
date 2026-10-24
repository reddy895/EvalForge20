"""Unit tests verifying timeout propagation from EvaluationConfig down to inference provider."""

import pytest

from src.evalforge.experiments.case_runner import CaseRunner
from src.evalforge.experiments.snapshot import FrozenTestCase
from src.evalforge.providers.mock import MockProvider
from src.evalforge.providers.schemas import InferenceRequest
from src.evalforge.schemas.evaluation import EvaluationConfig


@pytest.mark.asyncio
async def test_inference_request_timeout_propagation():
    """Verify CaseRunner passes timeout_seconds from EvaluationConfig into InferenceRequest."""
    mock = MockProvider(latency_seconds=0.001)
    config = EvaluationConfig(timeout_seconds=42.0)
    runner = CaseRunner(provider=mock, model_id="mock-llama-3.1-8b", config=config)

    case = FrozenTestCase(
        id="c1",
        dataset_id="d1",
        prompt="Test prompt",
        expected_output="Out",
    )

    result = await runner.execute_case(case, "eval-1")
    assert result is not None
    assert len(mock.call_history) == 1
    req = mock.call_history[0]
    assert req.timeout == 42.0


@pytest.mark.asyncio
async def test_mock_provider_timeout_enforcement():
    """Verify MockProvider triggers TimeoutError when latency exceeds request timeout."""
    mock = MockProvider(latency_seconds=0.05)
    req = InferenceRequest(model="mock-llama-3.1-8b", prompt="Hello", timeout=0.01)

    with pytest.raises(TimeoutError) as exc_info:
        await mock.generate(req)

    assert "Mock request timed out after 0.01s" in str(exc_info.value)
