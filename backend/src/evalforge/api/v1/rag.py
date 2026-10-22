"""API endpoints for RAG evaluation and context audit."""

from fastapi import APIRouter, status

from src.evalforge.schemas.rag import RAGEvaluationRequest, RAGEvaluationResponse
from src.evalforge.services.rag_service import RAGService

rag_router = APIRouter(prefix="/rag", tags=["RAG Evaluation"])


@rag_router.post(
    "/evaluate",
    response_model=RAGEvaluationResponse,
    status_code=status.HTTP_200_OK,
    summary="Evaluate RAG queries across context relevance, faithfulness, and citations",
)
async def evaluate_rag_suite(payload: RAGEvaluationRequest) -> RAGEvaluationResponse:
    """Score retrieval precision, answer grounding, and factual hallucinations on RAG cases."""
    return await RAGService.evaluate_suite(payload)
