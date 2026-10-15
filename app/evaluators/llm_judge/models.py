"""Domain schemas and validation models for Local LLM-as-Judge evaluators."""

from pydantic import BaseModel, ConfigDict, Field


class JudgeRubric(BaseModel):
    """Specification of an explicit scoring rubric for LLM-as-Judge evaluation."""

    model_config = ConfigDict(frozen=True)

    rubric_id: str = Field(..., description="Unique rubric identifier")
    name: str = Field(..., description="Human-readable title")
    version: str = Field(default="1.0.0", description="Semantic version of rubric guidelines")
    criteria: str = Field(..., description="Core criteria evaluated by judge")
    scale_min: int = Field(default=1, description="Minimum integer rating scale")
    scale_max: int = Field(default=5, description="Maximum integer rating scale")
    score_definitions: dict[int, str] = Field(
        default_factory=dict,
        description="Mapping from numeric score to detailed level description",
    )
    pass_threshold: float = Field(default=3.0, description="Minimum score to count as passed")


class JudgeEvaluationOutput(BaseModel):
    """Validated structured output payload expected from judge LLM inference."""

    model_config = ConfigDict(extra="ignore")

    score: float = Field(..., description="Numeric score awarded by the judge")
    passed: bool = Field(default=True, description="Whether the response meets rubric standards")
    explanation: str = Field(default="", description="Detailed qualitative rationale")
    confidence: float | None = Field(
        default=None, description="Self-reported confidence level (0.0 to 1.0)"
    )
