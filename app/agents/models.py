"""Domain models and schemas for AI Agent evaluation and structured execution traces."""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class AgentToolCall(BaseModel):
    """Specification of a tool call invoked by an agent."""

    model_config = ConfigDict(frozen=True)

    tool_name: str = Field(..., description="Name of the selected tool")
    arguments: dict[str, Any] = Field(
        default_factory=dict, description="Arguments passed to the tool"
    )
    call_id: str | None = Field(default=None, description="Optional unique invocation ID")


class AgentToolResult(BaseModel):
    """Execution outcome of a single tool invocation."""

    model_config = ConfigDict(frozen=True)

    tool_name: str
    call_id: str | None = None
    success: bool = True
    output: Any = None
    error: str | None = None


class AgentStepTrace(BaseModel):
    """A single discrete step in an agent's execution trajectory."""

    model_config = ConfigDict(frozen=True)

    step_index: int = Field(..., ge=0, description="0-indexed step sequence number")
    action_type: str = Field(
        ..., description="Action category (e.g. 'tool_call', 'thought', 'final_answer')"
    )
    thought: str | None = Field(default=None, description="Optional agent reasoning or thought log")
    tool_call: AgentToolCall | None = None
    tool_result: AgentToolResult | None = None
    duration_ms: float = Field(default=0.0, ge=0.0)


class AgentExecutionTrace(BaseModel):
    """Complete structured trace of an agent task run."""

    model_config = ConfigDict(frozen=True)

    agent_name: str = Field(..., description="Name or identifier of the evaluated agent")
    task_id: str = Field(..., description="Evaluation case or task identifier")
    steps: list[AgentStepTrace] = Field(default_factory=list, description="Ordered execution steps")
    final_answer: str | None = Field(
        default=None, description="Final response returned to user/evaluator"
    )
    completed: bool = Field(
        default=False, description="Whether agent successfully finished task execution"
    )
    total_duration_ms: float = Field(default=0.0, ge=0.0)
    errors: list[str] = Field(default_factory=list, description="Errors recorded during execution")

    @property
    def tool_names_invoked(self) -> list[str]:
        """List of tool names invoked across all steps in order."""
        return [s.tool_call.tool_name for s in self.steps if s.tool_call is not None]

    @property
    def step_count(self) -> int:
        return len(self.steps)
