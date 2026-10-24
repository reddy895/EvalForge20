"""Unit tests for RAG evaluators — Context Relevance, Faithfulness, and Answer Relevance."""

import pytest

from src.evalforge.evaluators.rag import (
    AnswerRelevanceEvaluator,
    ContextRelevanceEvaluator,
    FaithfulnessEvaluator,
    evaluate_rag_case,
)
from src.evalforge.schemas.rag import RAGQueryCase


class TestRAGEvaluators:
    """Verifies retrieval and hallucination grounding metrics for RAG pipelines."""

    @pytest.mark.asyncio
    async def test_context_relevance_high_coverage(self) -> None:
        evaluator = ContextRelevanceEvaluator()
        query = "What is the capital of France?"
        context = "The capital of France is Paris, with a large population."

        res = await evaluator.evaluate(prediction=context, reference=query)
        assert res.passed is True
        assert res.score >= 0.5
        assert res.details["matched_tokens"] > 0

    @pytest.mark.asyncio
    async def test_context_relevance_irrelevant_context_fails(self) -> None:
        evaluator = ContextRelevanceEvaluator()
        query = "What is the capital of France?"
        context = "The quick brown fox jumps over the lazy dog in the forest."

        res = await evaluator.evaluate(prediction=context, reference=query)
        assert res.passed is False
        assert res.score == 0.0

    @pytest.mark.asyncio
    async def test_faithfulness_grounded_answer(self) -> None:
        evaluator = FaithfulnessEvaluator()
        context = "Python was designed by Guido van Rossum and released in 1991."
        answer = "Guido van Rossum created Python in 1991."

        res = await evaluator.evaluate(prediction=answer, context=context)
        assert res.passed is True
        assert res.score >= 0.6
        assert res.method == "answer_grounding_coverage"

    @pytest.mark.asyncio
    async def test_faithfulness_hallucinated_answer_fails(self) -> None:
        evaluator = FaithfulnessEvaluator()
        context = "Python was released in 1991 by Guido."
        answer = "James Gosling invented Java at Sun Microsystems."

        res = await evaluator.evaluate(prediction=answer, context=context)
        assert res.passed is False
        assert res.score == 0.0

    @pytest.mark.asyncio
    async def test_answer_relevance_matching_query(self) -> None:
        evaluator = AnswerRelevanceEvaluator()
        query = "Explain quantum entanglement simply"
        answer = "Quantum entanglement occurs when two particles become interconnected regardless of distance."

        res = await evaluator.evaluate(prediction=answer, reference=query)
        assert res.passed is True
        assert res.score >= 0.5

    @pytest.mark.asyncio
    async def test_composite_rag_case_scorecard(self) -> None:
        case = RAGQueryCase(
            query="When was the Eiffel Tower completed?",
            retrieved_contexts=["The Eiffel Tower was completed in 1889 in Paris."],
            answer="The Eiffel Tower was completed in 1889.",
        )

        scorecard = await evaluate_rag_case(case)
        assert scorecard.context_relevance >= 0.5
        assert scorecard.faithfulness >= 0.6
        assert scorecard.answer_relevance >= 0.5
        assert scorecard.overall_score >= 0.5
