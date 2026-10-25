"""Unit tests for CodeExecutionEvaluator security sandbox, execution timeouts, and test suites."""

import pytest

from src.evalforge.evaluators.deterministic.code_execution import (
    CodeExecutionEvaluator,
    extract_python_code,
)


def test_extract_python_code_markdown_blocks() -> None:
    text_with_fences = "Here is the code:\n```python\ndef solve(x):\n    return x * 2\n```\nHope that helps!"
    extracted = extract_python_code(text_with_fences)
    assert extracted == "def solve(x):\n    return x * 2"

    raw_code = "def add(a, b):\n    return a + b"
    assert extract_python_code(raw_code) == raw_code
    assert extract_python_code("") == ""


@pytest.mark.asyncio
async def test_code_execution_passing_palindrome() -> None:
    evaluator = CodeExecutionEvaluator()
    code = """
def is_palindrome(s):
    clean = "".join(ch.lower() for ch in s if ch.isalnum())
    return clean == clean[::-1]
"""
    result = await evaluator.evaluate(prediction=code, function_name="is_palindrome")
    assert result.passed is True
    assert result.score == 1.0
    assert result.details["passed_count"] > 0
    assert result.details["failed_count"] == 0


@pytest.mark.asyncio
async def test_code_execution_failing_logic() -> None:
    evaluator = CodeExecutionEvaluator()
    code = """
def reverse_string(s):
    return s  # Wrong: not reversed
"""
    result = await evaluator.evaluate(prediction=code, function_name="reverse_string")
    assert result.passed is False
    assert result.score == 0.0
    assert result.details["error_type"] == "assertion_failure"


@pytest.mark.asyncio
async def test_code_execution_syntax_error() -> None:
    evaluator = CodeExecutionEvaluator()
    invalid_code = "def broken(\n  return 42"
    result = await evaluator.evaluate(prediction=invalid_code, function_name="broken")
    assert result.passed is False
    assert result.score == 0.0
    assert result.details["error_type"] == "invalid_code"
    assert "SyntaxError" in result.details["error"]


@pytest.mark.asyncio
async def test_code_execution_security_prohibits_dangerous_imports() -> None:
    evaluator = CodeExecutionEvaluator()
    malicious_code = """
import os

def list_files():
    return os.listdir(".")
"""
    result = await evaluator.evaluate(prediction=malicious_code, function_name="list_files")
    assert result.passed is False
    assert result.score == 0.0
    assert result.details["error_type"] == "security_violation"
    assert "prohibited" in result.details["error"].lower()


@pytest.mark.asyncio
async def test_code_execution_security_prohibits_eval_and_open() -> None:
    evaluator = CodeExecutionEvaluator()
    dangerous_code = """
def hack():
    f = open("/etc/passwd", "r")
    return f.read()
"""
    result = await evaluator.evaluate(prediction=dangerous_code, function_name="hack")
    assert result.passed is False
    assert result.score == 0.0
    assert result.details["error_type"] == "security_violation"


@pytest.mark.asyncio
async def test_code_execution_timeout_prevention() -> None:
    evaluator = CodeExecutionEvaluator(timeout_seconds=0.1)
    loop_code = """
import time

def slow_fn(n):
    time.sleep(1.0)
    return n
"""
    result = await evaluator.evaluate(
        prediction=loop_code,
        function_name="slow_fn",
        test_cases=[{"args": (1,), "expected": 1}],
    )
    assert result.passed is False
    assert result.score == 0.0
    assert result.details["error_type"] == "timeout"
