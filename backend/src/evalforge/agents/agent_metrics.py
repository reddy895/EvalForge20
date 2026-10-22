"""Agent evaluation metrics for tool selection, schema validity, and safety adherence."""

from pydantic import BaseModel

from src.evalforge.schemas.agent import AgentStepTrace


class AgentEvaluationScorecard(BaseModel):
    tool_accuracy: float
    schema_validity: float
    policy_violations: int
    task_completed: bool
    total_steps: int
    avg_step_duration_ms: float


def compute_agent_metrics(
    traces: list[AgentStepTrace],
    expected_tools: list[str] | None = None,
    expected_outcome: str | None = None,
    final_output: str | None = None,
    policy_violations: int = 0,
    raw_task_completed: bool = False,
) -> AgentEvaluationScorecard:
    """Calculate quantitative agent behavior metrics across recorded step traces."""
    tool_traces = [t for t in traces if t.tool_name is not None]
    total_tool_calls = len(tool_traces)

    # 1. Tool Selection Accuracy
    if not expected_tools:
        tool_accuracy = 1.0 if total_tool_calls > 0 else 0.5
    else:
        expected_set = {t.lower() for t in expected_tools}
        correct_calls = sum(
            1 for t in tool_traces if t.tool_name and t.tool_name.lower() in expected_set
        )
        tool_accuracy = round(correct_calls / total_tool_calls, 4) if total_tool_calls > 0 else 0.0

    # 2. Argument Schema Validity
    if total_tool_calls == 0:
        schema_validity = 1.0
    else:
        valid_calls = sum(1 for t in tool_traces if t.is_valid_call)
        schema_validity = round(valid_calls / total_tool_calls, 4)

    # 3. Final Task Completion
    task_completed = raw_task_completed
    if expected_outcome and final_output:
        if expected_outcome.lower() not in final_output.lower():
            task_completed = False

    # 4. Latency
    durations = [t.duration_ms for t in traces]
    avg_duration = round(sum(durations) / len(durations), 2) if durations else 0.0

    return AgentEvaluationScorecard(
        tool_accuracy=tool_accuracy,
        schema_validity=schema_validity,
        policy_violations=policy_violations,
        task_completed=task_completed,
        total_steps=len(traces),
        avg_step_duration_ms=avg_duration,
    )
