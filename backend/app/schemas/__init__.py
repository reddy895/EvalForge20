"""Pydantic request and response schemas for EvalForge20."""

from backend.app.schemas.comparisons import (
    ComparisonRow,
    ModelComparisonRequest,
    ModelComparisonResult,
)
from backend.app.schemas.evaluations import (
    AggregateMetrics,
    CaseMetricResult,
    CaseResult,
    EvaluationCase,
    EvaluationRunCreate,
    EvaluationRunDetail,
    EvaluationRunSummary,
)
from backend.app.schemas.models import (
    BenchmarkResult,
    HardwareRequirements,
    ModelPricing,
    ModelProfile,
    ModelSummary,
    OllamaModelPullRequest,
    OllamaModelPullResponse,
    OllamaStatusReport,
)
from backend.app.schemas.recommendations import (
    HardwareProfileInput,
    ModelRecommendation,
    TaskRecommendationRequest,
    TaskRecommendationResponse,
)

__all__ = [
    "BenchmarkResult",
    "HardwareRequirements",
    "ModelPricing",
    "ModelProfile",
    "ModelSummary",
    "OllamaModelPullRequest",
    "OllamaModelPullResponse",
    "OllamaStatusReport",
    "AggregateMetrics",
    "CaseMetricResult",
    "CaseResult",
    "EvaluationCase",
    "EvaluationRunCreate",
    "EvaluationRunDetail",
    "EvaluationRunSummary",
    "HardwareProfileInput",
    "ModelRecommendation",
    "TaskRecommendationRequest",
    "TaskRecommendationResponse",
    "ComparisonRow",
    "ModelComparisonRequest",
    "ModelComparisonResult",
]
