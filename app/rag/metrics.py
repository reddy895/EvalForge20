"""RAG evaluation metrics for retrieval performance and grounded generation."""

import re

from app.domain.contracts import EvaluatorContract, EvaluatorInput
from app.domain.results import MetricResult
from app.evaluators.registry import MetricCategory, MetricDefinition, registry
from app.rag.models import RetrievedChunk


def _extract_retrieved_chunks(eval_input: EvaluatorInput) -> list[RetrievedChunk]:
    """Extract retrieved chunks from case metadata or input options."""
    raw = (
        eval_input.case.metadata.get("retrieved_chunks")
        or eval_input.case.metadata.get("retrieved_contexts")
        or eval_input.options.get("retrieved_chunks")
        or []
    )
    chunks: list[RetrievedChunk] = []
    for item in raw:
        if isinstance(item, RetrievedChunk):
            chunks.append(item)
        elif isinstance(item, dict):
            chunks.append(
                RetrievedChunk(
                    doc_id=str(item.get("doc_id", f"doc_{len(chunks)}")),
                    text=str(item.get("text", "")),
                    score=item.get("score"),
                    metadata=item.get("metadata", {}),
                )
            )
        elif isinstance(item, str):
            chunks.append(
                RetrievedChunk(
                    doc_id=f"doc_{len(chunks)}",
                    text=item,
                )
            )
    return chunks


def _extract_ground_truth_ids(eval_input: EvaluatorInput) -> list[str] | None:
    """Extract ground truth document IDs from case metadata or options."""
    ids = (
        eval_input.case.metadata.get("ground_truth_doc_ids")
        or eval_input.case.metadata.get("relevant_doc_ids")
        or eval_input.options.get("ground_truth_doc_ids")
    )
    if ids is not None and isinstance(ids, list):
        return [str(x) for x in ids]
    return None


class ContextPrecisionAtKEvaluator(EvaluatorContract):
    """Measures the proportion of retrieved documents in top K that are relevant."""

    @property
    def metric_id(self) -> str:
        return "context_precision_at_k"

    @property
    def metric_name(self) -> str:
        return "Context Precision @ K"

    async def evaluate(self, eval_input: EvaluatorInput) -> MetricResult:
        k = int(eval_input.options.get("k", eval_input.case.metadata.get("k", 5)))
        gt_ids = _extract_ground_truth_ids(eval_input)
        if gt_ids is None or len(gt_ids) == 0:
            return MetricResult(
                metric_id=self.metric_id,
                metric_name=self.metric_name,
                score=None,
                passed=None,
                reason="Missing ground_truth_doc_ids in case metadata",
                is_model_based=False,
            )

        chunks = _extract_retrieved_chunks(eval_input)
        top_k = chunks[:k]
        if not top_k:
            return MetricResult(
                metric_id=self.metric_id,
                metric_name=self.metric_name,
                score=0.0,
                passed=False,
                reason=f"No retrieved chunks available for top-{k}",
                details={"k": k, "retrieved_count": 0},
                is_model_based=False,
            )

        gt_set = set(gt_ids)
        hits = sum(1 for c in top_k if c.doc_id in gt_set)
        score = round(hits / len(top_k), 4)

        threshold = float(eval_input.options.get("threshold", 0.5))
        passed = score >= threshold

        return MetricResult(
            metric_id=self.metric_id,
            metric_name=self.metric_name,
            score=score,
            passed=passed,
            reason=f"{hits}/{len(top_k)} top-{k} chunks were relevant ({score:.2%})",
            details={"k": k, "hits": hits, "total_examined": len(top_k), "threshold": threshold},
            is_model_based=False,
        )


class ContextRecallAtKEvaluator(EvaluatorContract):
    """Measures the proportion of relevant ground truth documents retrieved in top K."""

    @property
    def metric_id(self) -> str:
        return "context_recall_at_k"

    @property
    def metric_name(self) -> str:
        return "Context Recall @ K"

    async def evaluate(self, eval_input: EvaluatorInput) -> MetricResult:
        k = int(eval_input.options.get("k", eval_input.case.metadata.get("k", 5)))
        gt_ids = _extract_ground_truth_ids(eval_input)
        if gt_ids is None or len(gt_ids) == 0:
            return MetricResult(
                metric_id=self.metric_id,
                metric_name=self.metric_name,
                score=None,
                passed=None,
                reason="Missing ground_truth_doc_ids in case metadata",
                is_model_based=False,
            )

        chunks = _extract_retrieved_chunks(eval_input)
        top_k_ids = {c.doc_id for c in chunks[:k]}
        gt_set = set(gt_ids)
        hits = len(top_k_ids & gt_set)
        score = round(hits / len(gt_set), 4)

        threshold = float(eval_input.options.get("threshold", 0.8))
        passed = score >= threshold

        return MetricResult(
            metric_id=self.metric_id,
            metric_name=self.metric_name,
            score=score,
            passed=passed,
            reason=f"Retrieved {hits}/{len(gt_set)} relevant documents in top-{k} ({score:.2%})",
            details={
                "k": k,
                "hits": hits,
                "ground_truth_count": len(gt_set),
                "threshold": threshold,
            },
            is_model_based=False,
        )


class HitRateAtKEvaluator(EvaluatorContract):
    """Evaluates whether at least one relevant document is retrieved in top K (1.0 or 0.0)."""

    @property
    def metric_id(self) -> str:
        return "hit_rate_at_k"

    @property
    def metric_name(self) -> str:
        return "Hit Rate @ K"

    async def evaluate(self, eval_input: EvaluatorInput) -> MetricResult:
        k = int(eval_input.options.get("k", eval_input.case.metadata.get("k", 5)))
        gt_ids = _extract_ground_truth_ids(eval_input)
        if gt_ids is None or len(gt_ids) == 0:
            return MetricResult(
                metric_id=self.metric_id,
                metric_name=self.metric_name,
                score=None,
                passed=None,
                reason="Missing ground_truth_doc_ids in case metadata",
                is_model_based=False,
            )

        chunks = _extract_retrieved_chunks(eval_input)
        top_k_ids = {c.doc_id for c in chunks[:k]}
        has_hit = bool(top_k_ids & set(gt_ids))
        score = 1.0 if has_hit else 0.0

        return MetricResult(
            metric_id=self.metric_id,
            metric_name=self.metric_name,
            score=score,
            passed=has_hit,
            reason="Relevant document found in top-k"
            if has_hit
            else f"No relevant documents found in top-{k}",
            details={"k": k, "hit": has_hit},
            is_model_based=False,
        )


class MRREvaluator(EvaluatorContract):
    """Evaluates Reciprocal Rank of the first relevant document in top K (1 / rank)."""

    @property
    def metric_id(self) -> str:
        return "mrr_at_k"

    @property
    def metric_name(self) -> str:
        return "Reciprocal Rank @ K"

    async def evaluate(self, eval_input: EvaluatorInput) -> MetricResult:
        k = int(eval_input.options.get("k", eval_input.case.metadata.get("k", 5)))
        gt_ids = _extract_ground_truth_ids(eval_input)
        if gt_ids is None or len(gt_ids) == 0:
            return MetricResult(
                metric_id=self.metric_id,
                metric_name=self.metric_name,
                score=None,
                passed=None,
                reason="Missing ground_truth_doc_ids in case metadata",
                is_model_based=False,
            )

        chunks = _extract_retrieved_chunks(eval_input)
        gt_set = set(gt_ids)

        score = 0.0
        first_rank: int | None = None
        for rank, chunk in enumerate(chunks[:k], start=1):
            if chunk.doc_id in gt_set:
                score = round(1.0 / rank, 4)
                first_rank = rank
                break

        threshold = float(eval_input.options.get("threshold", 0.5))
        passed = score >= threshold

        return MetricResult(
            metric_id=self.metric_id,
            metric_name=self.metric_name,
            score=score,
            passed=passed,
            reason=f"First relevant document found at rank {first_rank} (RR={score:.4f})"
            if first_rank
            else f"No relevant document in top-{k}",
            details={"k": k, "first_rank": first_rank, "score": score},
            is_model_based=False,
        )


class GroundednessOverlapEvaluator(EvaluatorContract):
    """Evaluates deterministic token overlap between the generated answer and retrieved context chunks."""

    @property
    def metric_id(self) -> str:
        return "groundedness_overlap"

    @property
    def metric_name(self) -> str:
        return "Groundedness Token Overlap"

    async def evaluate(self, eval_input: EvaluatorInput) -> MetricResult:
        if not eval_input.actual_output or not eval_input.actual_output.strip():
            return MetricResult(
                metric_id=self.metric_id,
                metric_name=self.metric_name,
                score=0.0,
                passed=False,
                reason="Actual output is empty",
                is_model_based=False,
            )

        chunks = _extract_retrieved_chunks(eval_input)
        if not chunks:
            return MetricResult(
                metric_id=self.metric_id,
                metric_name=self.metric_name,
                score=None,
                passed=None,
                reason="No retrieved context chunks provided for groundedness check",
                is_model_based=False,
            )

        # Tokenize answer and combined context into word sets (excluding tiny stop words)
        def _get_words(text: str) -> set[str]:
            words = re.findall(r"\b[a-zA-Z0-9_-]{3,}\b", text.lower())
            return set(words)

        answer_tokens = _get_words(eval_input.actual_output)
        if not answer_tokens:
            return MetricResult(
                metric_id=self.metric_id,
                metric_name=self.metric_name,
                score=1.0,
                passed=True,
                reason="Answer contains no significant tokens to ground",
                is_model_based=False,
            )

        context_text = " ".join(c.text for c in chunks)
        context_tokens = _get_words(context_text)

        overlap = answer_tokens & context_tokens
        score = round(len(overlap) / len(answer_tokens), 4)

        threshold = float(eval_input.options.get("threshold", 0.6))
        passed = score >= threshold

        return MetricResult(
            metric_id=self.metric_id,
            metric_name=self.metric_name,
            score=score,
            passed=passed,
            reason=f"Answer groundedness overlap: {len(overlap)}/{len(answer_tokens)} tokens ({score:.2%})",
            details={
                "answer_token_count": len(answer_tokens),
                "context_token_count": len(context_tokens),
                "overlapping_token_count": len(overlap),
                "threshold": threshold,
            },
            is_model_based=False,
        )


# Register all RAG evaluators
registry.register(
    ContextPrecisionAtKEvaluator,
    MetricDefinition(
        metric_id="context_precision_at_k",
        metric_name="Context Precision @ K",
        description="Fraction of top-K retrieved context documents that are relevant according to ground truth IDs.",
        category=MetricCategory.RAG,
        requires_expected_output=False,
    ),
)
registry.register(
    ContextRecallAtKEvaluator,
    MetricDefinition(
        metric_id="context_recall_at_k",
        metric_name="Context Recall @ K",
        description="Fraction of all relevant ground truth documents that were successfully retrieved in top K.",
        category=MetricCategory.RAG,
        requires_expected_output=False,
    ),
)
registry.register(
    HitRateAtKEvaluator,
    MetricDefinition(
        metric_id="hit_rate_at_k",
        metric_name="Hit Rate @ K",
        description="Binary indicator (1.0/0.0) of whether at least one relevant document was retrieved in top K.",
        category=MetricCategory.RAG,
        requires_expected_output=False,
    ),
)
registry.register(
    MRREvaluator,
    MetricDefinition(
        metric_id="mrr_at_k",
        metric_name="Reciprocal Rank @ K",
        description="Reciprocal rank of the first relevant document in the top-K retrieved results.",
        category=MetricCategory.RAG,
        requires_expected_output=False,
    ),
)
registry.register(
    GroundednessOverlapEvaluator,
    MetricDefinition(
        metric_id="groundedness_overlap",
        metric_name="Groundedness Token Overlap",
        description="Deterministic token overlap ratio between the generated answer and retrieved context chunks.",
        category=MetricCategory.RAG,
        requires_expected_output=False,
    ),
)
