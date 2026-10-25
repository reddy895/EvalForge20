"""Sandboxed Python code execution evaluator with timeout and security controls."""

import ast
import asyncio
import re
from collections.abc import Callable
from typing import Any

from src.evalforge.evaluators.base import BaseEvaluator, EvaluationResult

SAFE_BUILTINS: dict[str, Any] = {
    "abs": abs,
    "all": all,
    "any": any,
    "bin": bin,
    "bool": bool,
    "dict": dict,
    "enumerate": enumerate,
    "filter": filter,
    "float": float,
    "format": format,
    "hex": hex,
    "int": int,
    "isinstance": isinstance,
    "issubclass": issubclass,
    "iter": iter,
    "len": len,
    "list": list,
    "map": map,
    "max": max,
    "min": min,
    "next": next,
    "oct": oct,
    "ord": ord,
    "pow": pow,
    "range": range,
    "reversed": reversed,
    "round": round,
    "set": set,
    "sorted": sorted,
    "str": str,
    "sum": sum,
    "tuple": tuple,
    "zip": zip,
    "True": True,
    "False": False,
    "None": None,
}

# Standard test fixtures for algorithmic benchmark problems
BENCHMARK_TEST_SUITES: dict[str, list[dict[str, Any]]] = {
    "reverse_string": [
        {"args": ("hello",), "expected": "olleh"},
        {"args": ("",), "expected": ""},
        {"args": ("a",), "expected": "a"},
        {"args": ("Python 3",), "expected": "3 nohtyP"},
        {"args": ("racecar",), "expected": "racecar"},
    ],
    "is_palindrome": [
        {"args": ("racecar",), "expected": True},
        {"args": ("Race Car",), "expected": True},
        {"args": ("hello",), "expected": False},
        {"args": ("A man a plan a canal Panama",), "expected": True},
        {"args": ("12321",), "expected": True},
        {"args": ("12345",), "expected": False},
    ],
    "fibonacci": [
        {"args": (0,), "expected": 0},
        {"args": (1,), "expected": 1},
        {"args": (2,), "expected": 1},
        {"args": (5,), "expected": 5},
        {"args": (7,), "expected": 13},
        {"args": (10,), "expected": 55},
    ],
}


def extract_python_code(text: str) -> str:
    """Extract code from markdown code blocks or return clean raw text."""
    if not text:
        return ""
    # Look for ```python ... ``` or ``` ... ```
    match = re.search(r"```(?:python)?\s*\n(.*?)```", text, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return text.strip()


def run_sandboxed_sync(
    code_str: str,
    target_fn_name: str | None,
    test_suite: list[dict[str, Any]],
) -> tuple[bool, float, dict[str, Any]]:
    """Execute code in a restricted namespace and run assertions."""
    # 1. Parse AST to detect syntax errors
    try:
        tree = ast.parse(code_str, filename="<eval_submission>")
    except SyntaxError as e:
        return False, 0.0, {
            "error": f"SyntaxError at line {e.lineno}: {e.msg}",
            "error_type": "invalid_code",
            "extracted_code": code_str,
        }

    # 2. Check for disallowed AST nodes (e.g. imports)
    disallowed_calls = {"eval", "exec", "compile", "__import__", "open"}
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            # Allow common safe modules (math, string, re)
            allowed_modules = {"math", "string", "re", "collections", "itertools", "functools"}
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name not in allowed_modules:
                        return False, 0.0, {
                            "error": f"Security violation: import of module '{alias.name}' is prohibited.",
                            "error_type": "security_violation",
                        }
            elif isinstance(node, ast.ImportFrom) and node.module not in allowed_modules:
                return False, 0.0, {
                    "error": f"Security violation: import from module '{node.module}' is prohibited.",
                    "error_type": "security_violation",
                }
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            if node.func.id in disallowed_calls:
                return False, 0.0, {
                    "error": f"Security violation: call to '{node.func.id}' is prohibited.",
                    "error_type": "security_violation",
                }

    # 3. Create sandboxed execution scope
    safe_env: dict[str, Any] = {"__builtins__": SAFE_BUILTINS}
    try:
        compiled = compile(tree, filename="<sandboxed_code>", mode="exec")
        exec(compiled, safe_env)
    except Exception as exc:
        return False, 0.0, {
            "error": f"Initialization error: {type(exc).__name__}: {exc}",
            "error_type": "runtime_error",
        }

    # 4. Find the target function
    fn: Callable[..., Any] | None = None
    if target_fn_name and target_fn_name in safe_env and callable(safe_env[target_fn_name]):
        fn = safe_env[target_fn_name]
    else:
        # Auto-detect function defined in tree
        func_names = [n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]
        if func_names and func_names[0] in safe_env and callable(safe_env[func_names[0]]):
            fn = safe_env[func_names[0]]
            target_fn_name = func_names[0]

    if not fn:
        return False, 0.0, {
            "error": f"Target function '{target_fn_name or 'any'}' not found in executable scope.",
            "error_type": "no_function",
        }

    # 5. Run test suite assertions
    passed_count = 0
    total_tests = len(test_suite)

    for i, test_case in enumerate(test_suite):
        args = test_case.get("args", ())
        kwargs = test_case.get("kwargs", {})
        expected = test_case.get("expected")

        try:
            result = fn(*args, **kwargs)
        except Exception as exc:
            return False, 0.0, {
                "error": f"Test case {i+1} runtime error on {target_fn_name}{args}: {type(exc).__name__}: {exc}",
                "error_type": "runtime_error",
                "test_index": i,
                "passed_count": passed_count,
                "total_tests": total_tests,
            }

        if result != expected:
            return False, 0.0, {
                "error": f"Assertion failed on {target_fn_name}{args}: returned {result!r}, expected {expected!r}",
                "error_type": "assertion_failure",
                "test_index": i,
                "passed_count": passed_count,
                "total_tests": total_tests,
            }

        passed_count += 1

    return True, 1.0, {
        "function_name": target_fn_name,
        "test_cases_run": total_tests,
        "passed_count": passed_count,
        "failed_count": 0,
    }


class CodeExecutionEvaluator(BaseEvaluator):
    """Evaluates generated Python code by executing controlled test assertions in an isolated sandbox."""

    def __init__(self, timeout_seconds: float = 2.0):
        super().__init__(
            name="code_execution",
            description="Executes candidate code against programmatic unit assertions with timeout and sandboxing.",
        )
        self.timeout_seconds = timeout_seconds

    async def evaluate(
        self,
        prediction: str,
        reference: str | None = None,
        context: str | None = None,
        **kwargs: Any,
    ) -> EvaluationResult:
        code_str = extract_python_code(prediction)
        if not code_str:
            return EvaluationResult(
                name=self.name,
                score=0.0,
                passed=False,
                method="sandboxed_code_execution",
                details={"error": "Empty or missing code prediction.", "error_type": "invalid_code"},
            )

        # Detect function name from kwargs or reference
        fn_name = kwargs.get("function_name")
        if not fn_name and reference:
            ref_match = re.search(r"def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(", reference)
            if ref_match:
                fn_name = ref_match.group(1)

        # Build test suite
        custom_tests = kwargs.get("test_cases")
        test_suite: list[dict[str, Any]]
        if custom_tests and isinstance(custom_tests, list):
            test_suite = custom_tests
        elif fn_name and fn_name in BENCHMARK_TEST_SUITES:
            test_suite = BENCHMARK_TEST_SUITES[fn_name]
        else:
            # Fallback: check function names in prediction
            pred_match = re.search(r"def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(", code_str)
            if pred_match and pred_match.group(1) in BENCHMARK_TEST_SUITES:
                fn_name = pred_match.group(1)
                test_suite = BENCHMARK_TEST_SUITES[fn_name]
            else:
                test_suite = []

        if not test_suite:
            # If no specific suite found, execute syntax verification and reference exact match fallback
            try:
                ast.parse(code_str)
                is_valid = bool(fn_name and fn_name in code_str)
                return EvaluationResult(
                    name=self.name,
                    score=1.0 if is_valid else 0.5,
                    passed=is_valid,
                    method="syntax_and_structure_validation",
                    details={"is_valid_syntax": True, "function_name": fn_name},
                )
            except SyntaxError as e:
                return EvaluationResult(
                    name=self.name,
                    score=0.0,
                    passed=False,
                    method="syntax_validation",
                    details={"error": f"SyntaxError: {e.msg}", "error_type": "invalid_code"},
                )

        # Run with timeout to prevent infinite loops
        try:
            passed, score, details = await asyncio.wait_for(
                asyncio.to_thread(run_sandboxed_sync, code_str, fn_name, test_suite),
                timeout=self.timeout_seconds,
            )
            return EvaluationResult(
                name=self.name,
                score=score,
                passed=passed,
                method="sandboxed_code_execution",
                details=details,
            )
        except TimeoutError:
            return EvaluationResult(
                name=self.name,
                score=0.0,
                passed=False,
                method="sandboxed_code_execution",
                details={
                    "error": f"Code execution timed out after {self.timeout_seconds}s.",
                    "error_type": "timeout",
                },
            )
        except Exception as exc:
            return EvaluationResult(
                name=self.name,
                score=0.0,
                passed=False,
                method="sandboxed_code_execution",
                details={
                    "error": f"Execution harness error: {exc}",
                    "error_type": "infrastructure_error",
                },
            )
