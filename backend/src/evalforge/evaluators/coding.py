"""Coding benchmarks, sandboxed Python code execution, and unit test pass-rate evaluators."""

from typing import Any

from src.evalforge.evaluators.base import BaseEvaluator, MetricResult
from src.evalforge.evaluators.deterministic.code_execution import (
    CodeExecutionEvaluator,
    extract_python_code,
    validate_code_security as validate_code_ast,
)


class FunctionalCorrectnessEvaluator(BaseEvaluator):
    """Evaluates Python code for syntax compilation, AST safety, and functional execution pass rate."""

    evaluator_id: str = "functional_correctness"
    name: str = "functional_correctness"
    version: str = "1.0.0"
    is_deterministic: bool = True
    required_inputs: list[str] = ["prediction"]

    def __init__(self, timeout_seconds: float = 3.0, **kwargs: Any) -> None:
        super().__init__(
            name="functional_correctness",
            evaluator_id="functional_correctness",
            description="Sandboxed unit test execution and AST compilation verification.",
            **kwargs,
        )
        self.inner = CodeExecutionEvaluator(timeout_seconds=timeout_seconds, **kwargs)

    async def evaluate(
        self,
        prediction: str,
        reference: str | None = None,
        context: str | None = None,
        problem_id: str | None = None,
        test_cases: list[dict[str, Any]] | None = None,
        **kwargs: Any,
    ) -> MetricResult:
        return await self.inner.evaluate(
            prediction=prediction,
            reference=reference,
            context=context,
            problem_id=problem_id,
            test_cases=test_cases,
            **kwargs,
        )


__all__ = [
    "CodeExecutionEvaluator",
    "FunctionalCorrectnessEvaluator",
    "extract_python_code",
    "validate_code_ast",
]
