"""Unit tests for TokenF1Evaluator — precision, recall, harmonic mean F1, and threshold rules."""

import pytest

from src.evalforge.evaluators.deterministic.token_f1 import TokenF1Evaluator


class TestTokenF1Evaluator:
    """Verifies token-level overlap precision, recall, and F1 calculations."""

    @pytest.fixture()
    def evaluator(self) -> TokenF1Evaluator:
        return TokenF1Evaluator()

    @pytest.mark.asyncio
    async def test_identical_text_yields_perfect_f1(self, evaluator: TokenF1Evaluator) -> None:
        text = "quick brown fox jumps"
        res = await evaluator.evaluate(prediction=text, reference=text)

        assert res.score == 1.0
        assert res.passed is True
        assert res.details["precision"] == 1.0
        assert res.details["recall"] == 1.0
        assert res.details["f1"] == 1.0
        assert res.details["shared_token_count"] == 4

    @pytest.mark.asyncio
    async def test_disjoint_tokens_yield_zero(self, evaluator: TokenF1Evaluator) -> None:
        res = await evaluator.evaluate(prediction="red blue", reference="green yellow")

        assert res.score == 0.0
        assert res.passed is False
        assert res.details["precision"] == 0.0
        assert res.details["recall"] == 0.0
        assert res.details["f1"] == 0.0

    @pytest.mark.asyncio
    async def test_superset_prediction_has_perfect_recall_lower_precision(
        self, evaluator: TokenF1Evaluator
    ) -> None:
        p = "the capital city of france is paris"
        r = "paris france"
        res = await evaluator.evaluate(prediction=p, reference=r)

        # 2 shared tokens: 'paris', 'france'
        # recall = 2/2 = 1.0; precision = 2/7 = 0.2857
        # f1 = 2 * (1.0 * 2/7) / (1.0 + 2/7) = (4/7) / (9/7) = 4/9 ≈ 0.4444
        assert res.details["recall"] == 1.0
        assert res.details["precision"] == pytest.approx(2 / 7, abs=0.01)
        assert res.score == pytest.approx(4 / 9, abs=0.01)

    @pytest.mark.asyncio
    async def test_subset_prediction_has_perfect_precision_lower_recall(
        self, evaluator: TokenF1Evaluator
    ) -> None:
        p = "paris france"
        r = "the capital city of france is paris"
        res = await evaluator.evaluate(prediction=p, reference=r)

        # precision = 2/2 = 1.0; recall = 2/7
        assert res.details["precision"] == 1.0
        assert res.details["recall"] == pytest.approx(2 / 7, abs=0.01)
        assert res.score == pytest.approx(4 / 9, abs=0.01)

    @pytest.mark.asyncio
    async def test_custom_threshold_controls_passing_status(
        self, evaluator: TokenF1Evaluator
    ) -> None:
        p = "paris france"
        r = "the capital city of france is paris"
        # F1 is ~0.4444
        res_pass = await evaluator.evaluate(prediction=p, reference=r, threshold=0.40)
        assert res_pass.passed is True

        res_fail = await evaluator.evaluate(prediction=p, reference=r, threshold=0.50)
        assert res_fail.passed is False

    @pytest.mark.asyncio
    async def test_missing_reference_fails(self, evaluator: TokenF1Evaluator) -> None:
        res = await evaluator.evaluate(prediction="Answer", reference=None)

        assert res.score == 0.0
        assert res.passed is False
        assert "No reference" in res.details["reason"]

    @pytest.mark.asyncio
    async def test_empty_prediction_and_reference(self, evaluator: TokenF1Evaluator) -> None:
        res = await evaluator.evaluate(prediction="", reference="")

        assert res.score == 1.0
        assert res.passed is True
