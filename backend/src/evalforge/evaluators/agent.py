"""Agent task completion and tool-calling correctness evaluators."""

import json
from typing import Any

from src.evalforge.evaluators.base import BaseEvaluator, MetricResult


class AgentToolCallEvaluator(BaseEvaluator):
    """Evaluates whether agent correctly selected and parameterized tools."""

    evaluator_id: str = "agent_tool_calling"
    name: str = "agent_tool_calling"
    version: str = "1.0.0"
    is_deterministic: bool = True
    required_inputs: list[str] = ["prediction"]

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(
            name="agent_tool_calling",
            evaluator_id="agent_tool_calling",
            description="Evaluates tool selection accuracy and parameter validity for AI agents.",
            **kwargs,
        )

    async def evaluate(
        self,
        prediction: str,
        reference: str | None = None,
        context: str | None = None,
        expected_tool_name: str | None = None,
        expected_arguments: dict[str, Any] | None = None,
        tool_calls: list[dict[str, Any]] | None = None,
        **kwargs: Any,
    ) -> MetricResult:
        calls = tool_calls or []
        if not calls:
            # Try to parse tool call from JSON in prediction
            try:
                parsed = json.loads(str(prediction))
                if isinstance(parsed, dict) and ("name" in parsed or "function" in parsed):
                    calls = [parsed]
            except Exception:
                pass

        if not expected_tool_name:
            passed = len(calls) > 0
            score = 1.0 if passed else 0.0
            return MetricResult(
                name=self.name,
                score=score,
                passed=passed,
                method="tool_call_presence",
                details={"tool_calls_count": len(calls)},
            )

        matched_tool = False
        args_correct = False

        for c in calls:
            name = c.get("name") or (c.get("function", {}).get("name") if isinstance(c.get("function"), dict) else None)
            if name and name.lower() == expected_tool_name.lower():
                matched_tool = True
                if expected_arguments:
                    args = c.get("arguments") or (c.get("function", {}).get("arguments") if isinstance(c.get("function"), dict) else {})
                    if isinstance(args, str):
                        try:
                            args = json.loads(args)
                        except Exception:
                            args = {}
                    if isinstance(args, dict):
                        args_correct = all(args.get(k) == v for k, v in expected_arguments.items())
                else:
                    args_correct = True
                break

        passed = matched_tool and args_correct
        score = 1.0 if passed else (0.5 if matched_tool else 0.0)

        return MetricResult(
            name=self.name,
            score=score,
            passed=passed,
            method="tool_selection_and_argument_validation",
            details={
                "expected_tool": expected_tool_name,
                "matched_tool": matched_tool,
                "args_correct": args_correct,
            },
        )


class AgentTaskCompletionEvaluator(BaseEvaluator):
    """Evaluates whether agent successfully satisfied the overall goal without errors."""

    evaluator_id: str = "agent_task_completion"
    name: str = "agent_task_completion"
    version: str = "1.0.0"
    is_deterministic: bool = True
    required_inputs: list[str] = ["prediction"]

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(
            name="agent_task_completion",
            evaluator_id="agent_task_completion",
            description="Verifies overall task completion and goal fulfillment for agent workflows.",
            **kwargs,
        )

    async def evaluate(
        self,
        prediction: str,
        reference: str | None = None,
        context: str | None = None,
        expected_outcome: str | None = None,
        **kwargs: Any,
    ) -> MetricResult:
        pred_lower = str(prediction).lower()
        target = (expected_outcome or reference or "").lower().strip()

        if not target:
            passed = len(pred_lower) > 0
            score = 1.0 if passed else 0.0
        else:
            passed = target in pred_lower
            score = 1.0 if passed else 0.0

        return MetricResult(
            name=self.name,
            score=score,
            passed=passed,
            method="agent_goal_fulfillment",
            details={"task_completed": passed},
        )


__all__ = [
    "AgentToolCallEvaluator",
    "AgentTaskCompletionEvaluator",
]
