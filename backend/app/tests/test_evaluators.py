"""Unit tests for deterministic evaluators."""

from backend.app.evaluators.deterministic import (
    ExactMatchEvaluator,
    JsonValidityEvaluator,
    KeywordContainsEvaluator,
    NormalizedMatchEvaluator,
)


def test_exact_match():
    r1 = ExactMatchEvaluator.evaluate("hello world", "hello world")
    assert r1.passed is True
    assert r1.score == 1.0

    r2 = ExactMatchEvaluator.evaluate("hello world", "Hello World")
    assert r2.passed is False
    assert r2.score == 0.0


def test_normalized_match():
    r = NormalizedMatchEvaluator.evaluate("  Hello    World \n", "hello world")
    assert r.passed is True
    assert r.score == 1.0


def test_keyword_contains():
    text = "def is_palindrome(s: str) -> bool:\n    return s == s[::-1]"
    r = KeywordContainsEvaluator.evaluate(text, ["def is_palindrome", "return"])
    assert r.passed is True

    r_fail = KeywordContainsEvaluator.evaluate(text, ["def is_palindrome", "lambda_handler"])
    assert r_fail.passed is False
    assert r_fail.score == 0.5


def test_json_validity():
    r_valid, obj = JsonValidityEvaluator.evaluate('```json\n{"name": "Alice", "age": 30}\n```')
    assert r_valid.passed is True
    assert obj == {"name": "Alice", "age": 30}

    r_invalid, obj_err = JsonValidityEvaluator.evaluate(
        "Here is your output: {name: Alice, age: 30"
    )
    assert r_invalid.passed is False
    assert obj_err is None
