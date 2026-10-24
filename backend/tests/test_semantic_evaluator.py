"""Unit tests for SemanticSimilarityEvaluator — lexical n-gram Jaccard similarity and estimate flagging."""

import pytest

from src.evalforge.evaluators.semantic import SemanticSimilarityEvaluator


class TestSemanticSimilarityEvaluator:
    """Verifies that semantic similarity calculates token overlaps and marks results as estimates."""

    @pytest.fixture()
    def evaluator(self) -> SemanticSimilarityEvaluator:
        return SemanticSimilarityEvaluator()

    @pytest.mark.asyncio
    async def test_identical_texts_yield_perfect_score(
        self, evaluator: SemanticSimilarityEvaluator
    ) -> None:
        text = "The quick brown fox jumps over the lazy dog."
        res = await evaluator.evaluate(prediction=text, reference=text)

        assert res.score == 1.0
        assert res.passed is True
        assert res.method == "ngram_jaccard_similarity"
        assert res.details["is_estimate"] is True
        assert res.details["unigram_jaccard"] == 1.0
        assert res.details["bigram_jaccard"] == 1.0

    @pytest.mark.asyncio
    async def test_completely_disjoint_texts_yield_zero(
        self, evaluator: SemanticSimilarityEvaluator
    ) -> None:
        p = "Apples oranges bananas"
        r = "Quantum mechanics particle physics"
        res = await evaluator.evaluate(prediction=p, reference=r)

        assert res.score == 0.0
        assert res.passed is False
        assert res.details["unigram_jaccard"] == 0.0
        assert res.details["bigram_jaccard"] == 0.0

    @pytest.mark.asyncio
    async def test_partial_overlap_passes_above_custom_threshold(
        self, evaluator: SemanticSimilarityEvaluator
    ) -> None:
        p = "Paris is the capital of France"
        r = "The capital of France is Paris"
        res = await evaluator.evaluate(prediction=p, reference=r, threshold=0.60)

        # Unigrams match 100%, bigrams have different order
        assert res.details["unigram_jaccard"] == 1.0
        assert res.score >= 0.60
        assert res.passed is True

    @pytest.mark.asyncio
    async def test_missing_reference_fails(
        self, evaluator: SemanticSimilarityEvaluator
    ) -> None:
        res = await evaluator.evaluate(prediction="Some answer", reference=None)

        assert res.score == 0.0
        assert res.passed is False
        assert "No reference" in res.details["reason"]

    @pytest.mark.asyncio
    async def test_empty_prediction_and_reference(
        self, evaluator: SemanticSimilarityEvaluator
    ) -> None:
        res = await evaluator.evaluate(prediction="", reference="")

        assert res.score == 1.0
        assert res.passed is True

    @pytest.mark.asyncio
    async def test_punctuation_and_casing_insensitivity(
        self, evaluator: SemanticSimilarityEvaluator
    ) -> None:
        p = "Hello, world! How are you?"
        r = "hello world how are you"
        res = await evaluator.evaluate(prediction=p, reference=r)

        assert res.score == 1.0
        assert res.passed is True
