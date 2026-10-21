"""Pydantic v2 schemas for RAG (Retrieval-Augmented Generation) evaluations."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class RAGQueryCase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    query: str = Field(..., description="User query or retrieval question")
    retrieved_contexts: List[str] = Field(..., description="Ordered list of context documents retrieved from corpus")
    answer: str = Field(..., description="Candidate model response under evaluation")
    reference_answer: Optional[str] = Field(None, description="Optional ground truth reference answer")
    expected_citations: Optional[List[str]] = Field(None, description="Optional expected source citations or quotes")


class RAGScorecard(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    context_relevance: float
    faithfulness: float
    answer_relevance: float
    citation_precision: Optional[float] = None
    citation_recall: Optional[float] = None
    overall_score: float
    details: Dict[str, Any] = Field(default_factory=dict)


class RAGEvaluationRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    cases: List[RAGQueryCase] = Field(..., min_length=1, description="List of RAG test cases to evaluate")
    threshold: float = Field(default=0.7, ge=0.0, le=1.0)


class RAGEvaluationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    total_cases: int
    passed_cases: int
    average_scorecard: RAGScorecard
    case_scorecards: List[RAGScorecard]
