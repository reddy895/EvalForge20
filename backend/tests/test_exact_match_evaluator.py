"""Unit tests for ExactMatchEvaluator and NormalizedExactMatchEvaluator."""

import pytest

from src.evalforge.evaluators.deterministic.exact_match import (
    ExactMatchEvaluator,
    NormalizedExactMatchEvaluator,
)


class TestExactMatchEvaluator:
    """Verifies strict character-level string match evaluation."""

    @pytest.fixture()
    def evaluator(self) -> ExactMatchEvaluator:
        return ExactMatchEvaluator()

    @pytest.mark.asyncio
    async def test_exact_match_success(self, evaluator: ExactMatchEvaluator) -> None:
        res = await evaluator.evaluate(prediction="Paris", reference="Paris")
        assert res.passed is True
        assert res.score == 1.0
        assert res.method == "strict_string_equality"
        assert res.details["matched"] is True

    @pytest.mark.asyncio
    async def test_exact_match_trims_outer_whitespace(self, evaluator: ExactMatchEvaluator) -> None:
        res = await evaluator.evaluate(prediction="  Paris \n", reference="Paris")
        assert res.passed is True
        assert res.score == 1.0

    @pytest.mark.asyncio
    async def test_exact_match_case_sensitive(self, evaluator: ExactMatchEvaluator) -> None:
        res = await evaluator.evaluate(prediction="paris", reference="Paris")
        assert res.passed is False
        assert res.score == 0.0

    @pytest.mark.asyncio
    async def test_missing_reference_fails_gracefully(self, evaluator: ExactMatchEvaluator) -> None:
        res = await evaluator.evaluate(prediction="Paris", reference=None)
        assert res.passed is False
        assert res.score == 0.0
        assert "No reference" in res.details["reason"]

    @pytest.mark.asyncio
    async def test_empty_prediction_and_reference(self, evaluator: ExactMatchEvaluator) -> None:
        res = await evaluator.evaluate(prediction="", reference="")
        assert res.passed is True
        assert res.score == 1.0


class TestNormalizedExactMatchEvaluator:
    """Verifies robust normalized equality stripping articles, punctuation, and casing."""

    @pytest.fixture()
    def evaluator(self) -> NormalizedExactMatchEvaluator:
        return NormalizedExactMatchEvaluator()

    @pytest.mark.asyncio
    async def test_case_insensitivity(self, evaluator: NormalizedExactMatchEvaluator) -> None:
        res = await evaluator.evaluate(prediction="tHe PaRiS", reference="Paris")
        assert res.passed is True
        assert res.score == 1.0
        assert res.method == "normalized_text_equality"

    @pytest.mark.asyncio
    async def test_punctuation_stripping(self, evaluator: NormalizedExactMatchEvaluator) -> None:
        res = await evaluator.evaluate(prediction="Hello, World!?", reference="Hello World")
        assert res.passed is True
        assert res.score == 1.0

    @pytest.mark.asyncio
    async def test_article_stripping(self, evaluator: NormalizedExactMatchEvaluator) -> None:
        res = await evaluator.evaluate(prediction="It is a cat", reference="It is the cat")
        assert res.passed is True
        assert res.score == 1.0

    @pytest.mark.asyncio
    async def test_whitespace_collapsing(self, evaluator: NormalizedExactMatchEvaluator) -> None:
        res = await evaluator.evaluate(prediction="apple    banana \n  cherry", reference="apple banana cherry")
        assert res.passed is True
        assert res.score == 1.0

    @pytest.mark.asyncio
    async def test_semantic_mismatch_fails(self, evaluator: NormalizedExactMatchEvaluator) -> None:
        res = await evaluator.evaluate(prediction="Paris, France", reference="London, UK")
        assert res.passed is False
        assert res.score == 0.0

    @pytest.mark.asyncio
    async def test_missing_reference_fails(self, evaluator: NormalizedExactMatchEvaluator) -> None:
        res = await evaluator.evaluate(prediction="Paris", reference=None)
        assert res.passed is False
        assert res.score == 0.0
