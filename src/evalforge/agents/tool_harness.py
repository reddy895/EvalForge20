"""Safe tool execution harness enforcing strict allowlists, schemas, and sandboxing."""

import ast
import operator as op
import time
from typing import Any, Callable, Dict, List, Optional, Set
from pydantic import BaseModel, Field

from src.evalforge.core.logging import get_logger

logger = get_logger("evalforge.agents.harness")

# Safe math operators for calculator AST evaluation (NO python eval() or exec()!)
SAFE_OPERATORS = {
    ast.Add: op.add,
    ast.Sub: op.sub,
    ast.Mult: op.mul,
    ast.Div: op.truediv,
    ast.FloorDiv: op.floordiv,
    ast.Mod: op.mod,
    ast.Pow: op.pow,
    ast.USub: op.neg,
}


def safe_eval_math(expr: str) -> float:
    """Safely evaluate simple arithmetic expressions without arbitrary code execution."""
    def _eval(node: ast.AST) -> float:
        if isinstance(node, ast.Expression):
            return _eval(node.body)
        elif isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return float(node.value)
        elif isinstance(node, ast.BinOp) and type(node.op) in SAFE_OPERATORS:
            left = _eval(node.left)
            right = _eval(node.right)
            return SAFE_OPERATORS[type(node.op)](left, right)
        elif isinstance(node, ast.UnaryOp) and type(node.op) in SAFE_OPERATORS:
            return SAFE_OPERATORS[type(node.op)](_eval(node.operand))
        else:
            raise ValueError(f"Unsupported math syntax or operation: {type(node).__name__}")

    tree = ast.parse(expr.strip(), mode="eval")
    return _eval(tree)


class ToolExecutionResult(BaseModel):
    success: bool
    output: Optional[Any] = None
    error: Optional[str] = None
    duration_ms: float = 0.0
    policy_violation: bool = False


class SafeToolHarness:
    """Safe, sandboxed execution environment strictly forbidding dangerous OS operations."""

    def __init__(self) -> None:
        self._handlers: Dict[str, Callable[[Dict[str, Any]], Any]] = {}
        self._register_default_tools()

    def _register_default_tools(self) -> None:
        # 1. Calculator
        def _calc(args: Dict[str, Any]) -> Any:
            expression = args.get("expression") or args.get("query") or ""
            return {"result": safe_eval_math(str(expression))}

        # 2. String Reverser
        def _reverse(args: Dict[str, Any]) -> Any:
            text = str(args.get("text", ""))
            return {"reversed": text[::-1]}

        # 3. Weather Lookup (Deterministic Mock)
        def _weather(args: Dict[str, Any]) -> Any:
            city = str(args.get("city", "Paris")).strip().title()
            mock_data = {
                "Paris": {"temperature_c": 19, "condition": "Partly Cloudy"},
                "Tokyo": {"temperature_c": 22, "condition": "Sunny"},
                "New York": {"temperature_c": 16, "condition": "Breezy"},
                "London": {"temperature_c": 14, "condition": "Overcast"},
            }
            return mock_data.get(city, {"temperature_c": 20, "condition": "Clear"})

        # 4. Dictionary Lookup
        def _dict(args: Dict[str, Any]) -> Any:
            word = str(args.get("word", "")).lower()
            definitions = {
                "algorithm": "A step-by-step procedure for solving a problem or accomplishing a task.",
                "latency": "The time delay between a cause and the observable effect.",
                "deterministic": "An outcome that is completely predictable with no randomness.",
            }
            return {"definition": definitions.get(word, f"No dictionary entry found for '{word}'")}

        self.register_tool("calculator", _calc)
        self.register_tool("string_reverser", _reverse)
        self.register_tool("weather_lookup", _weather)
        self.register_tool("dictionary_lookup", _dict)

    def register_tool(self, name: str, handler: Callable[[Dict[str, Any]], Any]) -> None:
        """Register a safe tool handler."""
        self._handlers[name.lower()] = handler

    def execute(
        self,
        tool_name: str,
        args: Dict[str, Any],
        allowed_tools: Optional[Set[str]] = None,
    ) -> ToolExecutionResult:
        """Execute a tool while enforcing explicit allowlists and catching exceptions."""
        start_time = time.perf_counter()
        name_clean = tool_name.lower().strip()

        # Enforce allowlist check
        if allowed_tools is not None and name_clean not in allowed_tools:
            duration = (time.perf_counter() - start_time) * 1000
            return ToolExecutionResult(
                success=False,
                error=f"Policy violation: tool '{tool_name}' is not in the permitted allowlist {sorted(list(allowed_tools))}",
                duration_ms=round(duration, 2),
                policy_violation=True,
            )

        handler = self._handlers.get(name_clean)
        if not handler:
            duration = (time.perf_counter() - start_time) * 1000
            return ToolExecutionResult(
                success=False,
                error=f"Unknown tool '{tool_name}'. No sandboxed handler available.",
                duration_ms=round(duration, 2),
                policy_violation=True,
            )

        try:
            output = handler(args)
            duration = (time.perf_counter() - start_time) * 1000
            return ToolExecutionResult(
                success=True,
                output=output,
                duration_ms=round(duration, 2),
                policy_violation=False,
            )
        except Exception as exc:
            duration = (time.perf_counter() - start_time) * 1000
            return ToolExecutionResult(
                success=False,
                error=f"Tool execution failed: {exc}",
                duration_ms=round(duration, 2),
                policy_violation=False,
            )
