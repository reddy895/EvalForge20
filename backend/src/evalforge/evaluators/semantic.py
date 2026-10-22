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
