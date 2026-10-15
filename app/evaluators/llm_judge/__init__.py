"""Local LLM-as-a-Judge evaluators and rubrics powered by Ollama."""

from app.evaluators.llm_judge.judge import (
    LocalOllamaJudgeEvaluator,
    OllamaJudgeCorrectnessEvaluator,
    OllamaJudgeExplanationEvaluator,
    OllamaJudgeFaithfulnessEvaluator,
    OllamaJudgeRelevanceEvaluator,
)
from app.evaluators.llm_judge.models import (
    JudgeEvaluationOutput,
    JudgeRubric,
)
from app.evaluators.llm_judge.rubrics import (
    ANSWER_RELEVANCE_RUBRIC,
    BUILTIN_RUBRICS,
    CONTEXT_FAITHFULNESS_RUBRIC,
    EXPLANATION_QUALITY_RUBRIC,
    FACTUAL_CORRECTNESS_RUBRIC,
)

__all__ = [
    "ANSWER_RELEVANCE_RUBRIC",
    "BUILTIN_RUBRICS",
    "CONTEXT_FAITHFULNESS_RUBRIC",
    "EXPLANATION_QUALITY_RUBRIC",
    "FACTUAL_CORRECTNESS_RUBRIC",
    "JudgeEvaluationOutput",
    "JudgeRubric",
    "LocalOllamaJudgeEvaluator",
    "OllamaJudgeCorrectnessEvaluator",
    "OllamaJudgeExplanationEvaluator",
    "OllamaJudgeFaithfulnessEvaluator",
    "OllamaJudgeRelevanceEvaluator",
]
