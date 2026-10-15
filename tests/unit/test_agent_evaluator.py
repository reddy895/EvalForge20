"""Unit tests for AI Agent evaluation and deterministic mock agent runtime."""

import pytest
from app.agents.evaluator import (
    StepEfficiencyEvaluator,
    TaskCompletionEvaluator,
    ToolArgumentValidityEvaluator,
    ToolSelectionAccuracyEvaluator,
)
from app.agents.mock_agent import DeterministicMockAgent
from app.agents.models import AgentExecutionTrace, AgentStepTrace, AgentToolCall
from app.domain.contracts import EvaluatorInput
from app.domain.models import EvaluationCase
from app.evaluators.registry import MetricCategory, registry


def test_deterministic_mock_agent_allowlist():
    agent = DeterministicMockAgent(name="TestAgent", max_steps=3)

    # 1. Permitted tool: calculator
    trace = agent.run_task(
        task_id="t1",
        query="add 2 and 3",
        scripted_steps=[
            {"tool": "calculator", "args": {"a": 2, "b": 3, "op": "add"}, "final_answer": "5"}
        ],
    )
    assert trace.completed is True
    assert len(trace.steps) == 1
    assert trace.steps[0].tool_result is not None
    assert trace.steps[0].tool_result.output == 5.0

    # 2. Block unauthorized tool
    trace_blocked = agent.run_task(
        task_id="t2",
        query="run dangerous command",
        scripted_steps=[{"tool": "shell_exec", "args": {"cmd": "ls"}}],
    )
    assert trace_blocked.completed is False
    assert any("not in the permitted allowlist" in err for err in trace_blocked.errors)


def test_deterministic_mock_agent_step_limit():
    agent = DeterministicMockAgent(name="LimitedAgent", max_steps=2)
    trace = agent.run_task(
        task_id="t3",
        query="multi step loop",
        scripted_steps=[
            {"tool": "calculator", "args": {"a": 1, "b": 1}},
            {"tool": "calculator", "args": {"a": 2, "b": 2}},
            {"tool": "calculator", "args": {"a": 3, "b": 3}},  # Exceeds max_steps 2
        ],
    )
    assert trace.completed is False
    assert any("Exceeded max_steps limit" in err for err in trace.errors)


@pytest.mark.asyncio
async def test_agent_task_completion_evaluator():
    evaluator = TaskCompletionEvaluator()

    # Success case
    agent = DeterministicMockAgent()
    trace = agent.run_task(
        task_id="t4",
        query="query",
        scripted_steps=[
            {
                "tool": "calculator",
                "args": {"a": 10, "b": 5, "op": "multiply"},
                "final_answer": "50",
            }
        ],
    )
    case = EvaluationCase(
        id="c1",
        input="calculate 10 * 5",
        expected_output="50",
        metadata={"agent_trace": trace},
    )
    res = await evaluator.evaluate(EvaluatorInput(case=case, actual_output="50"))
    assert res.score == 1.0
    assert res.passed is True

    # Missing trace
    case_no_trace = EvaluationCase(id="c2", input="query")
    res_none = await evaluator.evaluate(EvaluatorInput(case=case_no_trace, actual_output="50"))
    assert res_none.score is None


@pytest.mark.asyncio
async def test_tool_selection_accuracy_evaluator():
    evaluator = ToolSelectionAccuracyEvaluator()

    trace = AgentExecutionTrace(
        agent_name="Agent",
        task_id="task_traj",
        steps=[
            AgentStepTrace(
                step_index=0,
                action_type="tool_call",
                tool_call=AgentToolCall(tool_name="search_kb"),
            ),
            AgentStepTrace(
                step_index=1,
                action_type="tool_call",
                tool_call=AgentToolCall(tool_name="format_output"),
            ),
        ],
        completed=True,
    )

    # 1. Exact match trajectory
    case_exact = EvaluationCase(
        id="c3",
        input="search and format",
        metadata={"agent_trace": trace, "expected_tools": ["search_kb", "format_output"]},
    )
    res_exact = await evaluator.evaluate(EvaluatorInput(case=case_exact, actual_output=""))
    assert res_exact.score == 1.0
    assert res_exact.passed is True

    # 2. Mismatch trajectory
    case_mismatch = EvaluationCase(
        id="c4",
        input="search and format",
        metadata={"agent_trace": trace, "expected_tools": ["search_kb", "calculator"]},
    )
    res_mismatch = await evaluator.evaluate(EvaluatorInput(case=case_mismatch, actual_output=""))
    assert res_mismatch.score == 0.5
    assert res_mismatch.passed is False


@pytest.mark.asyncio
async def test_tool_argument_validity_evaluator():
    evaluator = ToolArgumentValidityEvaluator()

    trace = AgentExecutionTrace(
        agent_name="Agent",
        task_id="task_args",
        steps=[
            AgentStepTrace(
                step_index=0,
                action_type="tool_call",
                tool_call=AgentToolCall(
                    tool_name="calculator", arguments={"a": 10, "b": 20, "op": "add"}
                ),
            ),
        ],
        completed=True,
    )

    # All required arguments present
    case_valid = EvaluationCase(
        id="c5",
        input="calc",
        metadata={
            "agent_trace": trace,
            "expected_arguments": {"calculator": ["a", "b", "op"]},
        },
    )
    res_valid = await evaluator.evaluate(EvaluatorInput(case=case_valid, actual_output=""))
    assert res_valid.score == 1.0
    assert res_valid.passed is True

    # Missing required argument 'op'
    case_invalid = EvaluationCase(
        id="c6",
        input="calc",
        metadata={
            "agent_trace": trace,
            "expected_arguments": {"calculator": ["a", "b", "op", "non_existent_arg"]},
        },
    )
    res_invalid = await evaluator.evaluate(EvaluatorInput(case=case_invalid, actual_output=""))
    assert res_invalid.score == 0.0
    assert res_invalid.passed is False


@pytest.mark.asyncio
async def test_step_efficiency_evaluator():
    evaluator = StepEfficiencyEvaluator()

    # 2 steps out of optimal 2 -> score 1.0
    trace_optimal = AgentExecutionTrace(
        agent_name="Agent",
        task_id="task_eff",
        steps=[
            AgentStepTrace(step_index=0, action_type="thought"),
            AgentStepTrace(step_index=1, action_type="final_answer"),
        ],
        completed=True,
    )
    case_opt = EvaluationCase(
        id="c7",
        input="efficient query",
        metadata={"agent_trace": trace_optimal, "optimal_steps": 2, "max_steps": 5},
    )
    res_opt = await evaluator.evaluate(EvaluatorInput(case=case_opt, actual_output=""))
    assert res_opt.score == 1.0
    assert res_opt.passed is True


def test_agent_evaluators_registered():
    agent_metrics = [
        "agent_task_completion",
        "tool_selection_accuracy",
        "tool_argument_validity",
        "step_efficiency",
    ]
    for m in agent_metrics:
        assert registry.is_registered(m)
        defn = registry.get_definition(m)
        assert defn.category == MetricCategory.AGENT
