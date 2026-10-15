"""RAG evaluation models and schemas for retrieval and groundedness assessment."""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class RetrievedChunk(BaseModel):
    """Normalized representation of a retrieved document or chunk in a RAG pipeline."""

    model_config = ConfigDict(frozen=True)

    doc_id: str = Field(..., description="Unique document or chunk identifier")
    text: str = Field(..., description="Retrieved passage or chunk text")
    score: float | None = Field(default=None, description="Retrieval similarity or reranking score")
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Metadata associated with chunk"
    )


class RAGContext(BaseModel):
    """Context container extracted from an evaluation case."""

    query: str
    retrieved_chunks: list[RetrievedChunk]
    ground_truth_doc_ids: list[str] | None = None
    expected_answer: str | None = None
