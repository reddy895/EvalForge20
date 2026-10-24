"""Unit tests for evaluator deterministic modules — exact match, token F1, keyword, and JSON schema."""

import pytest

from src.evalforge.evaluators.deterministic.exact_match import (
    ExactMatchEvaluator,
    NormalizedExactMatchEvaluator,
)
from src.evalforge.evaluators.deterministic.json_schema import JsonSchemaEvaluator
from src.evalforge.evaluators.deterministic.keywords import KeywordEvaluator
from src.evalforge.evaluators.deterministic.token_f1 import TokenF1Evaluator


class TestExactMatchEvaluator:
    @pytest.mark.asyncio
    async def test_exact_pass(self) -> None:
        ev = ExactMatchEvaluator()
        res = await ev.evaluate(prediction="Paris", reference="Paris")
        assert res.passed is True
        assert res.score == 1.0

    @pytest.mark.asyncio
    async def test_exact_fail(self) -> None:
        ev = ExactMatchEvaluator()
        res = await ev.evaluate(prediction="London", reference="Paris")
        assert res.passed is False
        assert res.score == 0.0

    @pytest.mark.asyncio
    async def test_case_sensitive(self) -> None:
        ev = ExactMatchEvaluator()
        res = await ev.evaluate(prediction="paris", reference="Paris")
        assert res.passed is False

    @pytest.mark.asyncio
    async def test_empty_strings_match(self) -> None:
        ev = ExactMatchEvaluator()
        res = await ev.evaluate(prediction="", reference="")
        assert res.passed is True


class TestNormalizedExactMatchEvaluator:
    @pytest.mark.asyncio
    async def test_normalized_case_insensitive(self) -> None:
        ev = NormalizedExactMatchEvaluator()
        res = await ev.evaluate(prediction="PARIS", reference="paris")
        assert res.passed is True

    @pytest.mark.asyncio
    async def test_normalized_strips_whitespace(self) -> None:
        ev = NormalizedExactMatchEvaluator()
        res = await ev.evaluate(prediction="  Paris  ", reference="Paris")
        assert res.passed is True

    @pytest.mark.asyncio
    async def test_normalized_fail_different_words(self) -> None:
        ev = NormalizedExactMatchEvaluator()
        res = await ev.evaluate(prediction="Berlin", reference="Paris")
        assert res.passed is False


class TestTokenF1Evaluator:
    @pytest.mark.asyncio
    async def test_perfect_match_score_one(self) -> None:
        ev = TokenF1Evaluator()
        res = await ev.evaluate(
            prediction="The capital of France is Paris",
            reference="The capital of France is Paris",
        )
        assert res.score == pytest.approx(1.0, abs=0.01)

    @pytest.mark.asyncio
    async def test_partial_overlap_score_between_zero_and_one(self) -> None:
        ev = TokenF1Evaluator()
        res = await ev.evaluate(
            prediction="France capital Paris",
            reference="The capital of France is Paris and it is beautiful",
        )
        assert 0.0 < res.score < 1.0

    @pytest.mark.asyncio
    async def test_no_overlap_score_zero(self) -> None:
        ev = TokenF1Evaluator()
        res = await ev.evaluate(prediction="cat dog", reference="sun moon star")
        assert res.score == pytest.approx(0.0, abs=0.01)

    @pytest.mark.asyncio
    async def test_empty_prediction_score_zero(self) -> None:
        ev = TokenF1Evaluator()
        res = await ev.evaluate(prediction="", reference="Something expected")
        assert res.score == pytest.approx(0.0, abs=0.01)


class TestKeywordEvaluator:
    @pytest.mark.asyncio
    async def test_all_keywords_present(self) -> None:
        ev = KeywordEvaluator()
        res = await ev.evaluate(
            prediction="def fibonacci(n): return n if n <= 1 else fibonacci(n-1) + fibonacci(n-2)",
            reference="fibonacci",
            required_keywords=["fibonacci", "return"],
        )
        assert res.passed is True
        assert res.score == 1.0

    @pytest.mark.asyncio
    async def test_missing_keyword_fails(self) -> None:
        ev = KeywordEvaluator()
        res = await ev.evaluate(
            prediction="some function body",
            reference="",
            required_keywords=["fibonacci"],
        )
        assert res.passed is False

    @pytest.mark.asyncio
    async def test_partial_keywords_partial_score(self) -> None:
        ev = KeywordEvaluator()
        res = await ev.evaluate(
            prediction="fibonacci defined here",
            reference="",
            required_keywords=["fibonacci", "recursive", "base_case"],
        )
        assert 0.0 < res.score < 1.0


class TestJsonSchemaEvaluator:
    @pytest.mark.asyncio
    async def test_valid_json_object_passes(self) -> None:
        ev = JsonSchemaEvaluator()
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "integer"},
            },
            "required": ["name", "age"],
        }
        res = await ev.evaluate(
            prediction='{"name": "Alice", "age": 28}',
            reference="",
            json_schema=schema,
        )
        assert res.passed is True

    @pytest.mark.asyncio
    async def test_missing_required_field_fails(self) -> None:
        ev = JsonSchemaEvaluator()
        schema = {
            "type": "object",
            "properties": {"name": {"type": "string"}, "age": {"type": "integer"}},
            "required": ["name", "age"],
        }
        res = await ev.evaluate(
            prediction='{"name": "Bob"}',
            reference="",
            json_schema=schema,
        )
        # Missing required field 'age' — should score < 1.0 or fail
        assert res.score < 1.0 or res.passed is False

    @pytest.mark.asyncio
    async def test_invalid_json_string_fails(self) -> None:
        ev = JsonSchemaEvaluator()
        res = await ev.evaluate(
            prediction="not json at all",
            reference="",
            json_schema={"type": "object"},
        )
        assert res.passed is False
        assert res.score == 0.0
