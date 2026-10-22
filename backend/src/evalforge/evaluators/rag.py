"""RAG evaluators for Context Relevance, Faithfulness, and Answer Relevance."""

import re
import string
from typing import Any

from src.evalforge.evaluators.base import BaseEvaluator, MetricResult
from src.evalforge.schemas.rag import RAGQueryCase, RAGScorecard


def clean_tokens(text: str) -> set[str]:
    """Tokenize and remove punctuation and short stop words."""
    clean = text.lower()
    clean = "".join(ch for ch in clean if ch not in set(string.punctuation))
    words = re.findall(r"\w+", clean)
    stop = {"the", "a", "an", "is", "in", "it", "to", "and", "of", "for", "on", "with"}
    return {w for w in words if len(w) > 2 and w not in stop}


class ContextRelevanceEvaluator(BaseEvaluator):
    """Evaluates whether retrieved documents contain pertinent lexical-semantic content for the query."""

    name = "rag_context_relevance"
    version = "1.0.0"
    is_deterministic = True

    async def evaluate(
        self,
        prediction: str,  # Context string
        reference: str | None = None,  # Query string
        context: str | None = None,
        **kwargs: Any,
    ) -> MetricResult:
        query = reference or ""
        doc = prediction

        q_tokens = clean_tokens(query)
        d_tokens = clean_tokens(doc)

        if not q_tokens:
            score = 1.0
        else:
            overlap = q_tokens & d_tokens
            score = round(len(overlap) / len(q_tokens), 4)

        return MetricResult(
            name=self.name,
            score=score,
            passed=score >= 0.5,
            method="query_context_token_coverage",
            details={
                "query_tokens_count": len(q_tokens),
                "matched_tokens": len(q_tokens & d_tokens),
            },
        )


class FaithfulnessEvaluator(BaseEvaluator):
    """Evaluates whether statements in the answer are grounded in the retrieved context."""

    name = "rag_faithfulness"
    version = "1.0.0"
    is_deterministic = True

    async def evaluate(
        self,
        prediction: str,  # Generated answer
        reference: str | None = None,
        context: str | None = None,  # Concatenated contexts
        **kwargs: Any,
    ) -> MetricResult:
        answer = prediction
        ctx = context or ""

        a_tokens = clean_tokens(answer)
        c_tokens = clean_tokens(ctx)

        if not a_tokens:
            score = 1.0
        elif not c_tokens:
            score = 0.0
        else:
            supported_tokens = a_tokens & c_tokens
            score = round(len(supported_tokens) / len(a_tokens), 4)

        return MetricResult(
            name=self.name,
            score=score,
            passed=score >= 0.6,
            method="answer_grounding_coverage",
            details={
                "answer_tokens_count": len(a_tokens),
                "grounded_tokens_count": len(a_tokens & c_tokens) if c_tokens else 0,
            },
        )


class AnswerRelevanceEvaluator(BaseEvaluator):
    """Evaluates whether the generated answer directly addresses the query topic."""

    name = "rag_answer_relevance"
    version = "1.0.0"
    is_deterministic = True

    async def evaluate(
        self,
        prediction: str,  # Answer
        reference: str | None = None,  # Query
        context: str | None = None,
        **kwargs: Any,
    ) -> MetricResult:
        query = reference or ""
        answer = prediction

        q_tokens = clean_tokens(query)
        a_tokens = clean_tokens(answer)

        if not q_tokens:
            score = 1.0
        else:
            overlap = q_tokens & a_tokens
            score = round(len(overlap) / len(q_tokens), 4)

        return MetricResult(
            name=self.name,
            score=score,
            passed=score >= 0.5,
            method="answer_query_relevance_overlap",
            details={"query_overlap_count": len(q_tokens & a_tokens)},
        )


async def evaluate_rag_case(case: RAGQueryCase) -> RAGScorecard:
    """Evaluate a single RAG test case across context relevance, faithfulness, and answer relevance."""
    joined_contexts = " ".join(case.retrieved_contexts)

    # 1. Context relevance
    cr_eval = ContextRelevanceEvaluator()
    cr_res = await cr_eval.evaluate(joined_contexts, reference=case.query)

    # 2. Faithfulness
    f_eval = FaithfulnessEvaluator()
    f_res = await f_eval.evaluate(case.answer, context=joined_contexts)

    # 3. Answer relevance
    ar_eval = AnswerRelevanceEvaluator()
    ar_res = await ar_eval.evaluate(case.answer, reference=case.query)

    # 4. Citations if expected
    cit_prec: float | None = None
    cit_rec: float | None = None
    if case.expected_citations:
        found = []
        ans_tokens = clean_tokens(case.answer)
        for cit in case.expected_citations:
            cit_tokens = clean_tokens(cit)
            if cit.lower() in case.answer.lower():
                found.append(cit)
            elif cit_tokens and len(cit_tokens & ans_tokens) / len(cit_tokens) >= 0.4:
                found.append(cit)
        cit_rec = round(len(found) / len(case.expected_citations), 2)
        cit_prec = 1.0 if found else 0.0

    # Composite overall score
    overall = round((cr_res.score * 0.3) + (f_res.score * 0.4) + (ar_res.score * 0.3), 4)

    return RAGScorecard(
        context_relevance=cr_res.score,
        faithfulness=f_res.score,
        answer_relevance=ar_res.score,
        citation_precision=cit_prec,
        citation_recall=cit_rec,
        overall_score=overall,
        details={
            "context_relevance_passed": cr_res.passed,
            "faithfulness_passed": f_res.passed,
            "answer_relevance_passed": ar_res.passed,
        },
    )
