"""Pydantic v2 schemas for agent evaluation, tools, step traces, and safety policies."""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class AgentToolSpec(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str = Field(..., description="Unique tool name (e.g. 'calculator', 'weather_lookup')")
    description: str = Field(..., description="Instructional description explaining tool purpose")
    parameters: dict[str, Any] = Field(
        default_factory=dict, description="JSON Schema object defining allowed parameters"
    )


class AgentStepTrace(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    step_number: int
    tool_name: str | None = None
    tool_args: dict[str, Any] = Field(default_factory=dict)
    tool_result: Any | None = None
    thought: str | None = None
    duration_ms: float = 0.0
    is_valid_call: bool = True


class AgentEvaluationCreateRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str | None = Field(None, description="Optional custom label for this evaluation run")
    model_id: str = Field(..., description="Target model identifier (e.g. 'llama3.2')")
    provider: str = Field(
        default="ollama", description="Provider for model inference ('ollama' or 'mock')"
    )
    task: str = Field(..., description="User prompt or instruction task for the agent to resolve")
    tools: list[AgentToolSpec] = Field(
        default_factory=list, description="Available sandboxed tool specifications"
    )
    expected_tools: list[str] | None = Field(
        None, description="Permitted or expected tool names in sequence"
    )
    expected_outcome: str | None = Field(
        None, description="Expected target outcome phrase or answer"
    )
    max_steps: int = Field(
        default=8, ge=1, le=20, description="Hard bound on maximum tool execution steps"
    )
    timeout_seconds: float = Field(
        default=30.0, ge=1.0, le=120.0, description="Hard timeout ceiling for task completion"
    )


class AgentEvaluationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    model_id: str
    provider: str
    task: str
    status: str
    total_steps: int
    max_steps: int
    task_completed: bool
    tool_accuracy: float | None = None
    schema_validity: float | None = None
    policy_violations: int = 0
    final_output: str | None = None
    error_message: str | None = None
    created_at: str


class AgentEvaluationDetailResponse(AgentEvaluationResponse):
    traces: list[AgentStepTrace] = Field(default_factory=list)
