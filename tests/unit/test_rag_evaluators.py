"""Unit tests for RAG evaluation metrics (retrieval quality and groundedness)."""

import pytest
from app.domain.contracts import EvaluatorInput
from app.domain.models import EvaluationCase
from app.evaluators.registry import MetricCategory, registry
from app.rag.metrics import (
    ContextPrecisionAtKEvaluator,
    ContextRecallAtKEvaluator,
    GroundednessOverlapEvaluator,
    HitRateAtKEvaluator,
    MRREvaluator,
)
from app.rag.models import RetrievedChunk


@pytest.mark.asyncio
async def test_context_precision_at_k():
    evaluator = ContextPrecisionAtKEvaluator()
    case = EvaluationCase(
        id="rag_1",
        input="What is EvalForge20?",
        metadata={
            "retrieved_chunks": [
                {"doc_id": "doc_1", "text": "EvalForge20 is a local-first platform"},
                {"doc_id": "doc_irrelevant", "text": "Unrelated topic"},
                {"doc_id": "doc_2", "text": "It supports Ollama and LangSmith"},
            ],
            "ground_truth_doc_ids": ["doc_1", "doc_2", "doc_3"],
            "k": 3,
        },
    )
    res = await evaluator.evaluate(EvaluatorInput(case=case, actual_output="dummy"))
    # 2 out of 3 top chunks are in ground truth -> 2/3 = 0.6667
    assert res.score == 0.6667
    assert res.passed is True
    assert res.details["hits"] == 2
    assert res.details["total_examined"] == 3


@pytest.mark.asyncio
async def test_context_precision_missing_ground_truth():
    evaluator = ContextPrecisionAtKEvaluator()
    case = EvaluationCase(id="rag_2", input="query without reference doc ids")
    res = await evaluator.evaluate(EvaluatorInput(case=case, actual_output="dummy"))
    assert res.score is None
    assert res.passed is None
    assert "Missing ground_truth_doc_ids" in (res.reason or "")


@pytest.mark.asyncio
async def test_context_recall_at_k():
    evaluator = ContextRecallAtKEvaluator()
    case = EvaluationCase(
        id="rag_3",
        input="List all features",
        metadata={
            "retrieved_chunks": [
                RetrievedChunk(doc_id="doc_1", text="text 1"),
                RetrievedChunk(doc_id="doc_irrelevant", text="irrelevant"),
            ],
            "ground_truth_doc_ids": ["doc_1", "doc_2", "doc_3", "doc_4"],
            "k": 2,
        },
    )
    res = await evaluator.evaluate(
        EvaluatorInput(case=case, actual_output="dummy", options={"threshold": 0.4})
    )
    # Retrieved 1 out of 4 -> 1/4 = 0.25 (threshold 0.4 -> passed=False)
    assert res.score == 0.25
    assert res.passed is False
    assert res.details["hits"] == 1
    assert res.details["ground_truth_count"] == 4


@pytest.mark.asyncio
async def test_hit_rate_at_k():
    evaluator = HitRateAtKEvaluator()
    case_hit = EvaluationCase(
        id="rag_4",
        input="query",
        metadata={
            "retrieved_chunks": [{"doc_id": "doc_noise"}, {"doc_id": "doc_target"}],
            "ground_truth_doc_ids": ["doc_target"],
            "k": 2,
        },
    )
    res_hit = await evaluator.evaluate(EvaluatorInput(case=case_hit, actual_output="dummy"))
    assert res_hit.score == 1.0
    assert res_hit.passed is True

    case_miss = EvaluationCase(
        id="rag_5",
        input="query",
        metadata={
            "retrieved_chunks": [{"doc_id": "doc_noise"}],
            "ground_truth_doc_ids": ["doc_target"],
            "k": 1,
        },
    )
    res_miss = await evaluator.evaluate(EvaluatorInput(case=case_miss, actual_output="dummy"))
    assert res_miss.score == 0.0
    assert res_miss.passed is False


@pytest.mark.asyncio
async def test_mrr_at_k():
    evaluator = MRREvaluator()
    case = EvaluationCase(
        id="rag_6",
        input="query",
        metadata={
            "retrieved_chunks": [
                {"doc_id": "noise_1"},
                {"doc_id": "doc_target"},  # 2nd position -> rank 2 -> RR = 0.5
                {"doc_id": "doc_target_2"},
            ],
            "ground_truth_doc_ids": ["doc_target"],
            "k": 3,
        },
    )
    res = await evaluator.evaluate(EvaluatorInput(case=case, actual_output="dummy"))
    assert res.score == 0.5
    assert res.passed is True
    assert res.details["first_rank"] == 2


@pytest.mark.asyncio
async def test_groundedness_overlap():
    evaluator = GroundednessOverlapEvaluator()
    case = EvaluationCase(
        id="rag_7",
        input="Who created Python?",
        metadata={
            "retrieved_chunks": [
                {"doc_id": "doc_1", "text": "Guido van Rossum conceived Python in the late 1980s."}
            ]
        },
    )
    # Output is well-grounded in the context passage
    res = await evaluator.evaluate(
        EvaluatorInput(
            case=case,
            actual_output="Guido van Rossum conceived Python in the late 1980s.",
            options={"threshold": 0.8},
        )
    )
    assert res.score is not None and res.score >= 0.8
    assert res.passed is True

    # Empty answer
    res_empty = await evaluator.evaluate(EvaluatorInput(case=case, actual_output=""))
    assert res_empty.score == 0.0
    assert res_empty.passed is False


def test_rag_evaluators_registered():
    rag_metrics = [
        "context_precision_at_k",
        "context_recall_at_k",
        "hit_rate_at_k",
        "mrr_at_k",
        "groundedness_overlap",
    ]
    for m in rag_metrics:
        assert registry.is_registered(m)
        defn = registry.get_definition(m)
        assert defn.category == MetricCategory.RAG
