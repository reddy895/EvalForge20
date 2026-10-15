"""AI Agent evaluators for measuring tool selection, argument validity, task completion, and step efficiency."""

from typing import Any

from app.agents.models import AgentExecutionTrace
from app.domain.contracts import EvaluatorContract, EvaluatorInput
from app.domain.results import MetricResult
from app.evaluators.registry import MetricCategory, MetricDefinition, registry


def _extract_agent_trace(eval_input: EvaluatorInput) -> AgentExecutionTrace | None:
    """Extract AgentExecutionTrace from case metadata or options."""
    raw = eval_input.case.metadata.get("agent_trace") or eval_input.options.get("agent_trace")
    if isinstance(raw, AgentExecutionTrace):
        return raw
    if isinstance(raw, dict):
        try:
            return AgentExecutionTrace.model_validate(raw)
        except Exception:
            return None
    return None


class TaskCompletionEvaluator(EvaluatorContract):
    """Evaluates whether an agent completed its task without unhandled failures and provided a valid final answer."""

    @property
    def metric_id(self) -> str:
        return "agent_task_completion"

    @property
    def metric_name(self) -> str:
        return "Agent Task Completion"

    async def evaluate(self, eval_input: EvaluatorInput) -> MetricResult:
        trace = _extract_agent_trace(eval_input)
        if not trace:
            return MetricResult(
                metric_id=self.metric_id,
                metric_name=self.metric_name,
                score=None,
                passed=None,
                reason="No agent_trace found in case metadata or options",
                is_model_based=False,
            )

        if not trace.completed:
            return MetricResult(
                metric_id=self.metric_id,
                metric_name=self.metric_name,
                score=0.0,
                passed=False,
                reason=f"Agent failed to complete task (errors: {trace.errors})",
                details={"errors": trace.errors, "steps": trace.step_count},
                is_model_based=False,
            )

        # Check final answer against expected output if reference exists
        expected = eval_input.case.expected_output
        if expected and trace.final_answer:
            answer_matches = expected.strip().lower() in trace.final_answer.strip().lower()
            score = 1.0 if answer_matches else 0.5
            passed = answer_matches
            reason = (
                "Task completed and final answer matched expected reference"
                if passed
                else "Task marked completed but answer differed from expected reference"
            )
        else:
            score = 1.0
            passed = True
            reason = "Agent marked task execution successfully completed"

        return MetricResult(
            metric_id=self.metric_id,
            metric_name=self.metric_name,
            score=score,
            passed=passed,
            reason=reason,
            details={"step_count": trace.step_count, "final_answer": trace.final_answer},
            is_model_based=False,
        )


class ToolSelectionAccuracyEvaluator(EvaluatorContract):
    """Evaluates whether the agent selected the expected tools in the correct order."""

    @property
    def metric_id(self) -> str:
        return "tool_selection_accuracy"

    @property
    def metric_name(self) -> str:
        return "Tool Selection Accuracy"

    async def evaluate(self, eval_input: EvaluatorInput) -> MetricResult:
        trace = _extract_agent_trace(eval_input)
        expected_tools = eval_input.case.metadata.get("expected_tools") or eval_input.options.get(
            "expected_tools"
        )
        if not expected_tools or not isinstance(expected_tools, list):
            return MetricResult(
                metric_id=self.metric_id,
                metric_name=self.metric_name,
                score=None,
                passed=None,
                reason="Missing expected_tools list in case metadata",
                is_model_based=False,
            )

        if not trace:
            return MetricResult(
                metric_id=self.metric_id,
                metric_name=self.metric_name,
                score=None,
                passed=None,
                reason="No agent_trace found in case metadata or options",
                is_model_based=False,
            )

        actual_tools = trace.tool_names_invoked
        expected_list = [str(t) for t in expected_tools]

        # Order-preserving trajectory match vs set overlap
        strict_order = bool(eval_input.options.get("strict_order", True))
        if strict_order:
            matches = sum(1 for a, b in zip(actual_tools, expected_list, strict=False) if a == b)
            max_len = max(len(actual_tools), len(expected_list))

            score = round(matches / max_len, 4) if max_len > 0 else 1.0
            passed = actual_tools == expected_list
            reason = (
                "Exact tool trajectory matched"
                if passed
                else f"Tool sequence mismatch: actual={actual_tools}, expected={expected_list}"
            )
        else:
            set_act = set(actual_tools)
            set_exp = set(expected_list)
            intersection = set_act & set_exp
            union = set_act | set_exp
            score = round(len(intersection) / len(union), 4) if union else 1.0
            passed = set_exp.issubset(set_act)
            reason = (
                f"Required tools invoked ({intersection})"
                if passed
                else f"Missing required tools: {set_exp - set_act}"
            )

        return MetricResult(
            metric_id=self.metric_id,
            metric_name=self.metric_name,
            score=score,
            passed=passed,
            reason=reason,
            details={
                "actual_tools": actual_tools,
                "expected_tools": expected_list,
                "strict_order": strict_order,
            },
            is_model_based=False,
        )


class ToolArgumentValidityEvaluator(EvaluatorContract):
    """Evaluates whether all tool invocations provided required arguments."""

    @property
    def metric_id(self) -> str:
        return "tool_argument_validity"

    @property
    def metric_name(self) -> str:
        return "Tool Argument Validity"

    async def evaluate(self, eval_input: EvaluatorInput) -> MetricResult:
        trace = _extract_agent_trace(eval_input)
        if not trace:
            return MetricResult(
                metric_id=self.metric_id,
                metric_name=self.metric_name,
                score=None,
                passed=None,
                reason="No agent_trace found in case metadata or options",
                is_model_based=False,
            )

        tool_calls = [s.tool_call for s in trace.steps if s.tool_call is not None]
        if not tool_calls:
            return MetricResult(
                metric_id=self.metric_id,
                metric_name=self.metric_name,
                score=1.0,
                passed=True,
                reason="Agent executed with zero tool calls; no arguments to validate",
                is_model_based=False,
            )

        expected_args_map: dict[str, Any] = (
            eval_input.case.metadata.get("expected_arguments")
            or eval_input.options.get("expected_arguments")
            or {}
        )

        valid_calls = 0
        total_calls = len(tool_calls)
        violations: list[str] = []

        for tc in tool_calls:
            # Check if expected keys are present
            req_keys = expected_args_map.get(tc.tool_name, [])
            if isinstance(req_keys, list):
                missing = [k for k in req_keys if k not in tc.arguments]
                if missing:
                    violations.append(f"Tool '{tc.tool_name}' missing arguments {missing}")
                else:
                    valid_calls += 1
            else:
                valid_calls += 1

        score = round(valid_calls / total_calls, 4)
        passed = valid_calls == total_calls

        return MetricResult(
            metric_id=self.metric_id,
            metric_name=self.metric_name,
            score=score,
            passed=passed,
            reason="All tool arguments were valid"
            if passed
            else f"Argument violations: {violations}",
            details={
                "valid_calls": valid_calls,
                "total_calls": total_calls,
                "violations": violations,
            },
            is_model_based=False,
        )


class StepEfficiencyEvaluator(EvaluatorContract):
    """Evaluates task execution efficiency relative to optimal and maximum permitted steps."""

    @property
    def metric_id(self) -> str:
        return "step_efficiency"

    @property
    def metric_name(self) -> str:
        return "Step Efficiency"

    async def evaluate(self, eval_input: EvaluatorInput) -> MetricResult:
        trace = _extract_agent_trace(eval_input)
        if not trace:
            return MetricResult(
                metric_id=self.metric_id,
                metric_name=self.metric_name,
                score=None,
                passed=None,
                reason="No agent_trace found in case metadata or options",
                is_model_based=False,
            )

        optimal_steps = int(
            eval_input.case.metadata.get(
                "optimal_steps", eval_input.options.get("optimal_steps", 2)
            )
        )
        max_steps = int(
            eval_input.case.metadata.get("max_steps", eval_input.options.get("max_steps", 10))
        )

        actual = trace.step_count
        if actual <= optimal_steps:
            score = 1.0
            passed = True
            reason = f"Execution achieved optimal efficiency ({actual} <= {optimal_steps} steps)"
        elif actual > max_steps:
            score = 0.0
            passed = False
            reason = f"Execution exceeded maximum allowed steps ({actual} > {max_steps})"
        else:
            # Scaled score between optimal and max
            score = round(optimal_steps / actual, 4)
            passed = True
            reason = f"Execution completed in {actual} steps (efficiency ratio {score:.2f})"

        return MetricResult(
            metric_id=self.metric_id,
            metric_name=self.metric_name,
            score=score,
            passed=passed,
            reason=reason,
            details={
                "actual_steps": actual,
                "optimal_steps": optimal_steps,
                "max_steps": max_steps,
            },
            is_model_based=False,
        )


# Register all Agent evaluators
registry.register(
    TaskCompletionEvaluator,
    MetricDefinition(
        metric_id="agent_task_completion",
        metric_name="Agent Task Completion",
        description="Assesses whether the agent finished execution cleanly and produced a valid final answer.",
        category=MetricCategory.AGENT,
        requires_expected_output=False,
    ),
)
registry.register(
    ToolSelectionAccuracyEvaluator,
    MetricDefinition(
        metric_id="tool_selection_accuracy",
        metric_name="Tool Selection Accuracy",
        description="Evaluates whether the agent invoked the expected tools in the correct trajectory order.",
        category=MetricCategory.AGENT,
        requires_expected_output=False,
    ),
)
registry.register(
    ToolArgumentValidityEvaluator,
    MetricDefinition(
        metric_id="tool_argument_validity",
        metric_name="Tool Argument Validity",
        description="Measures whether tool calls satisfied all required argument parameters.",
        category=MetricCategory.AGENT,
        requires_expected_output=False,
    ),
)
registry.register(
    StepEfficiencyEvaluator,
    MetricDefinition(
        metric_id="step_efficiency",
        metric_name="Step Efficiency",
        description="Measures agent execution efficiency relative to optimal and maximum step bounds.",
        category=MetricCategory.AGENT,
        requires_expected_output=False,
    ),
)
