"""Main unified Pydantic schemas for EvalForge20."""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ModelInfo(BaseModel):
    """Model metadata from local provider discovery."""

    model_config = ConfigDict(extra="ignore")

    id: str
    name: str
    provider: str = "ollama"
    model_identifier: str
    family: str | None = None
    parameter_count: str | None = None
    context_window: int = 4096
    is_local: bool = True
    is_installed: bool = True
    supports_tools: bool = False
    supports_structured_output: bool = True
    license: str | None = None
    description: str | None = None
    size_bytes: int | None = None


class ModelConnectionTestRequest(BaseModel):
    model_identifier: str
    provider: str = "ollama"
    prompt: str = "Hello, respond with 'OK'."


class ModelConnectionTestResponse(BaseModel):
    model_identifier: str
    status: Literal["connected", "error"]
    latency_ms: float
    response_sample: str | None = None
    error_message: str | None = None


class WorkflowNode(BaseModel):
    """Node in the visual n8n-style playground."""

    model_config = ConfigDict(extra="ignore")

    id: str
    type: Literal["model", "dataset", "evaluator", "benchmark"]
    name: str = ""
    category: str = ""
    data: dict[str, Any] = Field(default_factory=dict)
    position: dict[str, float] = Field(default_factory=lambda: {"x": 0.0, "y": 0.0})


class WorkflowEdge(BaseModel):
    """Edge connection between nodes in the visual canvas.

    Accepts both canonical (source/target) and legacy (source_id/target_id) field names
    so that the frontend serialiser and backend validator remain compatible.
    """

    model_config = ConfigDict(extra="ignore")

    id: str
    source: str = ""
    target: str = ""
    sourceHandle: str | None = None
    targetHandle: str | None = None

    @model_validator(mode="before")
    @classmethod
    def _normalise_source_target(cls, values: Any) -> Any:
        """Accept source_id/target_id as aliases for source/target."""
        if isinstance(values, dict):
            if "source" not in values or not values.get("source"):
                values["source"] = values.get("source_id", "")
            if "target" not in values or not values.get("target"):
                values["target"] = values.get("target_id", "")
        return values


class WorkflowGraph(BaseModel):
    """Full workflow canvas definition."""

    nodes: list[WorkflowNode] = Field(default_factory=list)
    edges: list[WorkflowEdge] = Field(default_factory=list)


class WorkflowCreateRequest(BaseModel):
    name: str
    description: str | None = None
    graph: WorkflowGraph


class WorkflowUpdateRequest(BaseModel):
    name: str | None = None
    description: str | None = None
    graph: WorkflowGraph | None = None
    is_active: bool | None = None


class WorkflowResponse(BaseModel):
    id: str
    name: str
    description: str | None = None
    graph: WorkflowGraph
    is_active: bool = True
    created_at: datetime
    updated_at: datetime


class WorkflowValidationError(BaseModel):
    node_id: str | None = None
    edge_id: str | None = None
    message: str
    severity: Literal["error", "warning"] = "error"


class WorkflowValidationResult(BaseModel):
    is_valid: bool
    errors: list[WorkflowValidationError] = Field(default_factory=list)
    warnings: list[WorkflowValidationError] = Field(default_factory=list)
    executable_models: list[str] = Field(default_factory=list)
    executable_evaluators: list[str] = Field(default_factory=list)
    dataset_records_count: int = 0


class ExecutionTriggerRequest(BaseModel):
    """Payload for POST /api/executions.

    Accepts both the canonical ``graph`` field and the frontend-serialised
    ``workflow_graph`` alias so that the playground can POST without changes.
    The ``name`` field is accepted as an alias for ``execution_name``.
    """

    model_config = ConfigDict(extra="ignore")

    workflow_id: str | None = None
    graph: WorkflowGraph | None = None
    # Frontend sends workflow_graph and name — accept both
    workflow_graph: WorkflowGraph | None = None
    execution_name: str | None = None
    name: str | None = None
    judge_model_identifier: str | None = None
    concurrency_limit: int = 4
    timeout_seconds: float = 60.0

    @model_validator(mode="after")
    def _normalise_graph_and_name(self) -> "ExecutionTriggerRequest":
        """Resolve workflow_graph → graph and name → execution_name."""
        if self.graph is None and self.workflow_graph is not None:
            self.graph = self.workflow_graph
        if self.execution_name is None and self.name is not None:
            self.execution_name = self.name
        return self


class ExecutionEvent(BaseModel):
    """SSE streamed execution progress event."""

    execution_id: str
    event_type: Literal[
        "started",
        "step_progress",
        "case_completed",
        "metric_calculated",
        "log",
        "completed",
        "failed",
        "cancelled",
    ]
    timestamp: str
    message: str
    progress_percentage: float = 0.0
    completed_steps: int = 0
    total_steps: int = 0
    data: dict[str, Any] = Field(default_factory=dict)


class ExecutionResponse(BaseModel):
    id: str
    workflow_id: str | None = None
    status: Literal["PENDING", "RUNNING", "COMPLETED", "FAILED", "CANCELLED"]
    total_steps: int = 0
    completed_steps: int = 0
    started_at: datetime
    completed_at: datetime | None = None
    error_message: str | None = None
    logs: list[str] = Field(default_factory=list)


class ExperimentResponse(BaseModel):
    id: str
    name: str
    workflow_id: str | None = None
    execution_id: str | None = None
    model_identifier: str
    dataset_id: str | None = None
    evaluator_ids: list[str] = Field(default_factory=list)
    metrics: dict[str, Any] = Field(default_factory=dict)
    parameters: dict[str, Any] = Field(default_factory=dict)
    hardware: dict[str, Any] = Field(default_factory=dict)
    status: str = "COMPLETED"
    created_at: datetime


class ExperimentCompareRequest(BaseModel):
    experiment_ids: list[str]


class ExperimentCompareResponse(BaseModel):
    experiments: list[ExperimentResponse]
    metric_comparison: dict[str, dict[str, float]] = Field(default_factory=dict)
    latency_comparison: dict[str, float] = Field(default_factory=dict)
    reliability_comparison: dict[str, float] = Field(default_factory=dict)
    efficiency_comparison: dict[str, dict[str, float]] = Field(default_factory=dict)


class LeaderboardEntry(BaseModel):
    rank: int
    model_identifier: str
    category: str
    benchmark_dataset: str
    score: float
    metric_name: str
    samples_count: int
    hardware: str
    latency_ms: float | None = None
    evaluated_at: str
    is_verified: bool = True


class LeaderboardResponse(BaseModel):
    category: str
    entries: list[LeaderboardEntry]
    total_models: int
