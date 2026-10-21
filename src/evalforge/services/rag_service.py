"""RAG evaluation service evaluating retrieval pipelines and factual faithfulness."""

from typing import List

from src.evalforge.evaluators.rag import evaluate_rag_case
from src.evalforge.schemas.rag import (
    RAGEvaluationRequest,
    RAGEvaluationResponse,
    RAGScorecard,
)


class RAGService:
    """Service evaluating retrieval accuracy and answer grounding for RAG systems."""

    @staticmethod
    async def evaluate_suite(request: RAGEvaluationRequest) -> RAGEvaluationResponse:
        """Score a collection of RAG test cases across grounding and retrieval metrics."""
        case_scorecards: List[RAGScorecard] = []
        passed_count = 0

        for case in request.cases:
            card = await evaluate_rag_case(case)
            case_scorecards.append(card)
            if card.overall_score >= request.threshold:
                passed_count += 1

        total = len(case_scorecards)
        avg_cr = round(sum(c.context_relevance for c in case_scorecards) / total, 4)
        avg_f = round(sum(c.faithfulness for c in case_scorecards) / total, 4)
        avg_ar = round(sum(c.answer_relevance for c in case_scorecards) / total, 4)
        avg_overall = round(sum(c.overall_score for c in case_scorecards) / total, 4)

        avg_scorecard = RAGScorecard(
            context_relevance=avg_cr,
            faithfulness=avg_f,
            answer_relevance=avg_ar,
            overall_score=avg_overall,
            details={"threshold": request.threshold, "total_cases": total},
        )

        return RAGEvaluationResponse(
            total_cases=total,
            passed_cases=passed_count,
            average_scorecard=avg_scorecard,
            case_scorecards=case_scorecards,
        )
