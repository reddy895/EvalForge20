"""Unit tests for local Ollama-powered LLM-as-a-Judge evaluators."""

import pytest
from app.config import Settings
from app.domain.contracts import EvaluatorInput, ProviderResponse
from app.domain.models import EvaluationCase
from app.evaluators.llm_judge.judge import (
    LocalOllamaJudgeEvaluator,
    OllamaJudgeCorrectnessEvaluator,
    OllamaJudgeExplanationEvaluator,
    OllamaJudgeFaithfulnessEvaluator,
    OllamaJudgeRelevanceEvaluator,
)
from app.evaluators.llm_judge.rubrics import (
    ANSWER_RELEVANCE_RUBRIC,
)
from app.evaluators.registry import MetricCategory, registry
from app.providers.ollama import OllamaProvider


@pytest.fixture
def base_case() -> EvaluationCase:
    return EvaluationCase(
        id="judge_case_1",
        input="Explain why the sky is blue.",
        expected_output="The sky appears blue due to Rayleigh scattering.",
        metadata={"context": "Rayleigh scattering causes shorter blue wavelengths to scatter more."},
    )


@pytest.mark.asyncio
async def test_judge_perfect_json_response(base_case: EvaluationCase, monkeypatch: pytest.MonkeyPatch):
    """Test judge successfully evaluates with standard structured JSON."""
    async def mock_generate(self, req):
        return ProviderResponse(
            output_text='{"score": 5, "passed": true, "explanation": "Directly and accurately explains Rayleigh scattering.", "confidence": 0.95}',
            latency_ms=120.0,
            is_success=True,
        )

    monkeypatch.setattr(OllamaProvider, "generate", mock_generate)

    evaluator = LocalOllamaJudgeEvaluator(rubric=ANSWER_RELEVANCE_RUBRIC)
    eval_input = EvaluatorInput(
        case=base_case,
        actual_output="The sky is blue because blue light is scattered in all directions by gas particles in Earth's atmosphere.",
    )

    result = await evaluator.evaluate(eval_input)

    assert result.metric_id == "ollama_judge_answer_relevance"
    assert result.is_model_based is True
    assert result.passed is True
    assert result.score == 1.0  # (5 - 1) / (5 - 1) = 1.0
    assert result.details["raw_score"] == 5.0
    assert result.details["confidence"] == 0.95
    assert "Directly and accurately explains" in result.reason


@pytest.mark.asyncio
async def test_judge_markdown_fence_extraction(base_case: EvaluationCase, monkeypatch: pytest.MonkeyPatch):
    """Test judge successfully extracts JSON enclosed in markdown code fences."""
    raw_markdown = """```json
{
  "score": 4,
  "passed": true,
  "explanation": "Mostly accurate with good detail.",
  "confidence": 0.85
}
```"""

    async def mock_generate(self, req):
        return ProviderResponse(
            output_text=raw_markdown,
            latency_ms=150.0,
            is_success=True,
        )

    monkeypatch.setattr(OllamaProvider, "generate", mock_generate)

    evaluator = OllamaJudgeRelevanceEvaluator()
    eval_input = EvaluatorInput(case=base_case, actual_output="Because of light scattering.")

    result = await evaluator.evaluate(eval_input)
    assert result.passed is True
    assert result.score == 0.75  # (4 - 1) / 4 = 0.75
    assert result.details["raw_score"] == 4.0


@pytest.mark.asyncio
async def test_judge_regex_fallback_recovery(base_case: EvaluationCase, monkeypatch: pytest.MonkeyPatch):
    """Test regex extraction when output is conversational rather than strict JSON."""
    conversational_output = (
        "Here is my assessment of the answer:\n"
        "Score: 3/5\n"
        "Explanation: The answer is partially complete but omits wavelength details."
    )

    async def mock_generate(self, req):
        return ProviderResponse(
            output_text=conversational_output,
            latency_ms=100.0,
            is_success=True,
        )

    monkeypatch.setattr(OllamaProvider, "generate", mock_generate)

    evaluator = LocalOllamaJudgeEvaluator(rubric=ANSWER_RELEVANCE_RUBRIC)
    eval_input = EvaluatorInput(case=base_case, actual_output="It scatters light.")

    result = await evaluator.evaluate(eval_input)
    assert result.passed is True  # 3.0 >= pass_threshold 3.0
    assert result.score == 0.5  # (3 - 1) / 4 = 0.5
    assert result.details["raw_score"] == 3.0


@pytest.mark.asyncio
async def test_judge_factual_correctness(base_case: EvaluationCase, monkeypatch: pytest.MonkeyPatch):
    """Test factual correctness evaluator scoring below threshold."""
    async def mock_generate(self, req):
        return ProviderResponse(
            output_text='{"score": 2, "passed": false, "explanation": "Claims the sky is blue because oceans reflect it, which is false.", "confidence": 0.99}',
            latency_ms=90.0,
            is_success=True,
        )

    monkeypatch.setattr(OllamaProvider, "generate", mock_generate)

    evaluator = OllamaJudgeCorrectnessEvaluator()
    eval_input = EvaluatorInput(
        case=base_case,
        actual_output="The sky is blue because it reflects the ocean waters.",
    )

    result = await evaluator.evaluate(eval_input)
    assert result.passed is False
    assert result.score == 0.25  # (2 - 1) / 4 = 0.25
    assert result.details["raw_score"] == 2.0


@pytest.mark.asyncio
async def test_judge_context_faithfulness(base_case: EvaluationCase, monkeypatch: pytest.MonkeyPatch):
    """Test context faithfulness evaluator using supplied context."""
    async def mock_generate(self, req):
        return ProviderResponse(
            output_text='{"score": 5, "passed": true, "explanation": "Every single claim is verified by the context.", "confidence": 1.0}',
            latency_ms=110.0,
            is_success=True,
        )

    monkeypatch.setattr(OllamaProvider, "generate", mock_generate)

    evaluator = OllamaJudgeFaithfulnessEvaluator()
    eval_input = EvaluatorInput(
        case=base_case,
        actual_output="Rayleigh scattering causes shorter blue wavelengths to scatter more.",
    )

    result = await evaluator.evaluate(eval_input)
    assert result.passed is True
    assert result.score == 1.0


@pytest.mark.asyncio
async def test_judge_unparseable_output_graceful_failure(base_case: EvaluationCase, monkeypatch: pytest.MonkeyPatch):
    """Test graceful error handling when output cannot be parsed into a score."""
    async def mock_generate(self, req):
        return ProviderResponse(
            output_text="I am not sure how to evaluate this prompt. Have a nice day!",
            latency_ms=80.0,
            is_success=True,
        )

    monkeypatch.setattr(OllamaProvider, "generate", mock_generate)

    evaluator = OllamaJudgeRelevanceEvaluator()
    eval_input = EvaluatorInput(case=base_case, actual_output="Test output.")

    result = await evaluator.evaluate(eval_input)
    assert result.passed is False
    assert result.score is None
    assert "Judge output could not be parsed" in result.reason


@pytest.mark.asyncio
async def test_judge_provider_error_handling(base_case: EvaluationCase, monkeypatch: pytest.MonkeyPatch):
    """Test provider connection failure or inference error handling."""
    async def mock_generate(self, req):
        return ProviderResponse(
            output_text="",
            latency_ms=10.0,
            is_success=False,
            error_message="Cannot connect to ollama daemon at 'http://localhost:11434'",
        )

    monkeypatch.setattr(OllamaProvider, "generate", mock_generate)

    evaluator = OllamaJudgeExplanationEvaluator()
    eval_input = EvaluatorInput(case=base_case, actual_output="Test output.")

    result = await evaluator.evaluate(eval_input)
    assert result.passed is False
    assert result.score is None
    assert "Judge model" in result.reason
    assert "execution failed" in result.reason


@pytest.mark.asyncio
async def test_judge_disabled_via_settings(base_case: EvaluationCase, monkeypatch: pytest.MonkeyPatch):
    """Test that when ENABLE_LOCAL_JUDGE=False, the evaluator returns skipped reason without invoking LLM."""
    monkeypatch.setattr(
        "app.evaluators.llm_judge.judge.get_settings",
        lambda: Settings(enable_local_judge=False),
    )

    evaluator = OllamaJudgeRelevanceEvaluator()
    eval_input = EvaluatorInput(case=base_case, actual_output="Test output.")

    result = await evaluator.evaluate(eval_input)
    assert result.score is None
    assert result.passed is None
    assert "Local LLM judge is disabled via configuration" in result.reason


def test_registry_contains_ollama_judges():
    """Verify local Ollama judges are registered in the global evaluator registry."""
    expected_judge_metrics = [
        "ollama_judge_answer_relevance",
        "ollama_judge_factual_correctness",
        "ollama_judge_context_faithfulness",
        "ollama_judge_explanation_quality",
    ]

    for metric_id in expected_judge_metrics:
        assert registry.is_registered(metric_id), f"Metric '{metric_id}' not found in registry"
        defn = registry.get_definition(metric_id)
        assert defn.category == MetricCategory.MODEL_BASED
        evaluator = registry.get(metric_id)
        assert isinstance(evaluator, LocalOllamaJudgeEvaluator)
