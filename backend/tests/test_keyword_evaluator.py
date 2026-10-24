"""Unit tests for KeywordEvaluator — required phrases, prohibited terms, and word boundary matching."""

import pytest

from src.evalforge.evaluators.deterministic.keywords import KeywordEvaluator


class TestKeywordEvaluator:
    """Verifies keyword compliance, prohibition enforcement, and word boundaries."""

    @pytest.fixture()
    def evaluator(self) -> KeywordEvaluator:
        return KeywordEvaluator()

    @pytest.mark.asyncio
    async def test_all_required_keywords_present(self, evaluator: KeywordEvaluator) -> None:
        text = "The system will utilize Postgres, Redis, and FastAPI for backend infrastructure."
        res = await evaluator.evaluate(
            prediction=text,
            required_keywords=["Postgres", "Redis", "FastAPI"],
        )
        assert res.passed is True
        assert res.score == 1.0
        assert res.details["missing_required"] == []
        assert len(res.details["found_required"]) == 3

    @pytest.mark.asyncio
    async def test_missing_required_keyword_fails(self, evaluator: KeywordEvaluator) -> None:
        text = "The system uses MySQL and FastAPI."
        res = await evaluator.evaluate(
            prediction=text,
            required_keywords=["Postgres", "FastAPI"],
        )
        assert res.passed is False
        assert res.score == 0.5  # 1 out of 2 found
        assert "Postgres" in res.details["missing_required"]
        assert "FastAPI" in res.details["found_required"]

    @pytest.mark.asyncio
    async def test_prohibited_keyword_causes_immediate_failure(
        self, evaluator: KeywordEvaluator
    ) -> None:
        text = "Here is the API key: sk-abcdef123456"
        res = await evaluator.evaluate(
            prediction=text,
            required_keywords=["API"],
            prohibited_keywords=["sk-abcdef123456"],
        )
        assert res.passed is False
        assert res.score == 0.0
        assert "sk-abcdef123456" in res.details["found_prohibited"]

    @pytest.mark.asyncio
    async def test_case_sensitivity_flag(self, evaluator: KeywordEvaluator) -> None:
        text = "The language is python."

        # Case-insensitive (default)
        res_ci = await evaluator.evaluate(
            prediction=text,
            required_keywords=["Python"],
            case_sensitive=False,
        )
        assert res_ci.passed is True

        # Case-sensitive
        res_cs = await evaluator.evaluate(
            prediction=text,
            required_keywords=["Python"],
            case_sensitive=True,
        )
        assert res_cs.passed is False

    @pytest.mark.asyncio
    async def test_any_keywords_condition(self, evaluator: KeywordEvaluator) -> None:
        text = "The sky is blue today."
        res = await evaluator.evaluate(
            prediction=text,
            any_keywords=["red", "green", "blue"],
        )
        assert res.passed is True
        assert res.score == 1.0
        assert "blue" in res.details["found_any"]

    @pytest.mark.asyncio
    async def test_word_boundaries_prevent_substring_false_positives(
        self, evaluator: KeywordEvaluator
    ) -> None:
        text = "The categorical data was updated."
        # 'cat' is a substring of 'categorical', but NOT a separate word
        res = await evaluator.evaluate(
            prediction=text,
            required_keywords=["cat"],
        )
        assert res.passed is False
        assert "cat" in res.details["missing_required"]
