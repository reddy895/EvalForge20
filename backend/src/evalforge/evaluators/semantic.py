"""Semantic and lexical similarity evaluator based on n-gram and Jaccard coefficients."""

import re
import string
from typing import Any

from src.evalforge.evaluators.base import BaseEvaluator, MetricResult


class SemanticSimilarityEvaluator(BaseEvaluator):
    """Computes lexical-semantic similarity using token n-gram Jaccard and Dice coefficients.

    Provides a fast, local-first similarity proxy without requiring external embedding models.
    """

    name = "semantic_similarity"
    version = "1.0.0"
    is_deterministic = True

    @staticmethod
    def get_ngrams(tokens: list[str], n: int) -> set[str]:
        if len(tokens) < n:
            return set(tokens)
        return {" ".join(tokens[i : i + n]) for i in range(len(tokens) - n + 1)}

    @staticmethod
    def clean_tokens(text: str) -> list[str]:
        clean = text.lower()
        clean = "".join(ch for ch in clean if ch not in set(string.punctuation))
        return re.findall(r"\w+", clean)

    async def evaluate(
        self,
        prediction: str,
        reference: str | None = None,
        context: str | None = None,
        threshold: float = 0.65,
        **kwargs: Any,
    ) -> MetricResult:
        if reference is None:
            return MetricResult(
                name=self.name,
                score=0.0,
                passed=False,
                method="ngram_jaccard_similarity",
                details={"reason": "No reference output provided for similarity calculation."},
            )

        p_tokens = self.clean_tokens(prediction)
        r_tokens = self.clean_tokens(reference)

        if not p_tokens or not r_tokens:
            score = 1.0 if not p_tokens and not r_tokens else 0.0
            return MetricResult(
                name=self.name,
                score=score,
                passed=score >= threshold,
                method="ngram_jaccard_similarity",
                details={"similarity": score},
            )

        # Unigrams & Bigrams sets
        p_uni = set(p_tokens)
        r_uni = set(r_tokens)
        uni_jaccard = len(p_uni & r_uni) / len(p_uni | r_uni)

        p_bi = self.get_ngrams(p_tokens, 2)
        r_bi = self.get_ngrams(r_tokens, 2)
        bi_jaccard = len(p_bi & r_bi) / len(p_bi | r_bi) if (p_bi | r_bi) else uni_jaccard

        # Blended similarity score (60% unigram + 40% bigram)
        combined_sim = round(0.6 * uni_jaccard + 0.4 * bi_jaccard, 4)
        passed = combined_sim >= threshold

        return MetricResult(
            name=self.name,
            score=combined_sim,
            passed=passed,
            method="ngram_jaccard_similarity",
            details={
                "is_estimate": True,
                "unigram_jaccard": round(uni_jaccard, 4),
                "bigram_jaccard": round(bi_jaccard, 4),
                "combined_similarity": combined_sim,
                "threshold": threshold,
            },
        )


class KeywordPresenceEvaluator(BaseEvaluator):
    """Verifies that all required keywords or key concepts appear in the model prediction."""

    evaluator_id: str = "keyword_presence"
    name: str = "keyword_presence"
    version: str = "1.0.0"
    is_deterministic: bool = True
    required_inputs: list[str] = ["prediction"]

    def __init__(self, required_keywords: list[str] | None = None, **kwargs: Any) -> None:
        super().__init__(
            name="keyword_presence",
            evaluator_id="keyword_presence",
            description="Verifies the presence of key terms and concepts in output text.",
            **kwargs,
        )
        self.required_keywords = required_keywords or []

    async def evaluate(
        self,
        prediction: str,
        reference: str | None = None,
        context: str | None = None,
        keywords: list[str] | None = None,
        **kwargs: Any,
    ) -> MetricResult:
        target_kws = keywords or self.required_keywords
        if not target_kws and reference:
            # Extract key nouns/terms from reference if no explicit list
            target_kws = [k for k in reference.lower().split() if len(k) > 4]

        if not target_kws:
            return MetricResult(
                name=self.name,
                score=1.0,
                passed=True,
                method="keyword_presence",
                details={"message": "No keywords specified for matching"},
            )

        pred_lower = str(prediction).lower()
        found = [kw for kw in target_kws if kw.lower() in pred_lower]
        missing = [kw for kw in target_kws if kw.lower() not in pred_lower]

        score = len(found) / len(target_kws) if target_kws else 1.0
        passed = len(missing) == 0

        return MetricResult(
            name=self.name,
            score=round(score, 4),
            passed=passed,
            method="keyword_containment",
            details={
                "total_keywords": len(target_kws),
                "found_keywords": found,
                "missing_keywords": missing,
            },
        )


__all__ = [
    "SemanticSimilarityEvaluator",
    "KeywordPresenceEvaluator",
]
