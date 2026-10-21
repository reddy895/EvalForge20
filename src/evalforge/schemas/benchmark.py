"""Pydantic v2 schemas for multi-model benchmark comparisons and matrix reports."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field

from src.evalforge.schemas.evaluation import EvaluationConfig


class ModelComparisonMetrics(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    model_id: str
    provider: str
    evaluation_id: str
    pass_rate: float
    passed_cases: int
    failed_cases: int
    total_cases: int
    avg_latency_ms: float
    p50_latency_ms: float
    p95_latency_ms: float
    avg_throughput_tok_s: Optional[float] = None
    total_tokens: Optional[int] = None
    metric_breakdown: Dict[str, float] = Field(default_factory=dict)


class ReproducibilityMetadata(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    dataset_id: str
    dataset_version: int
    dataset_snapshot_hash: str
    metrics_evaluated: List[str]
    temperature: float
    concurrency: int
    executed_at: str
    disclaimer: str = (
        "Model comparisons are grounded solely in the selected dataset snapshot, "
        "inference parameters, and evaluation methodology."
    )


class BenchmarkCompareRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: Optional[str] = Field(None, description="Custom name for this benchmark comparison")
    dataset_id: str = Field(..., description="ID of the dataset to benchmark models against")
    models: List[str] = Field(..., min_length=1, description="List of model IDs to compare")
    provider: str = Field(default="ollama", description="Provider for inference (e.g. 'ollama' or 'mock')")
    config: Optional[EvaluationConfig] = Field(default_factory=EvaluationConfig)


class BenchmarkComparisonResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    dataset_id: str
    dataset_name: Optional[str] = None
    models: List[str]
    evaluation_ids: List[str]
    matrix: List[ModelComparisonMetrics]
    reproducibility: ReproducibilityMetadata
    created_at: str
