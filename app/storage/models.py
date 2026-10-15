"""SQLAlchemy ORM models for evaluation runs, cases, metrics, datasets, and comparisons."""

from datetime import UTC, datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.storage.database import Base


class DatasetModel(Base):
    """SQLAlchemy model for logical datasets."""

    __tablename__ = "datasets"

    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_json: Mapped[str] = mapped_column(Text, default="{}")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )
    latest_version: Mapped[int] = mapped_column(Integer, default=1)

    versions: Mapped[list["DatasetVersionModel"]] = relationship(
        "DatasetVersionModel", back_populates="dataset", cascade="all, delete-orphan"
    )


class DatasetVersionModel(Base):
    """SQLAlchemy model for versioned immutable dataset snapshots."""

    __tablename__ = "dataset_versions"

    version_id: Mapped[str] = mapped_column(String(100), primary_key=True)
    dataset_id: Mapped[str] = mapped_column(
        String(100), ForeignKey("datasets.id", ondelete="CASCADE"), index=True
    )
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    cases_json: Mapped[str] = mapped_column(Text, nullable=False)  # Serialized list of cases
    stats_json: Mapped[str] = mapped_column(Text, default="{}")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )

    dataset: Mapped["DatasetModel"] = relationship("DatasetModel", back_populates="versions")


class EvaluationRunModel(Base):
    """SQLAlchemy model for evaluation run executions."""

    __tablename__ = "evaluation_runs"

    run_id: Mapped[str] = mapped_column(String(100), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending", index=True)
    target_config_json: Mapped[str] = mapped_column(Text, nullable=False)
    evaluator_configs_json: Mapped[str] = mapped_column(Text, nullable=False)
    dataset_version_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    total_cases: Mapped[int] = mapped_column(Integer, default=0)
    completed_cases: Mapped[int] = mapped_column(Integer, default=0)
    failed_cases: Mapped[int] = mapped_column(Integer, default=0)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    aggregate_metrics_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    case_results: Mapped[list["CaseResultModel"]] = relationship(
        "CaseResultModel", back_populates="run", cascade="all, delete-orphan"
    )

    __table_args__ = (Index("idx_runs_started_at", "started_at"),)


class CaseResultModel(Base):
    """SQLAlchemy model for individual test case evaluation outcomes."""

    __tablename__ = "case_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    case_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    run_id: Mapped[str] = mapped_column(
        String(100), ForeignKey("evaluation_runs.run_id", ondelete="CASCADE"), index=True
    )
    input_json: Mapped[str] = mapped_column(Text, nullable=False)
    actual_output_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    expected_output_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    latency_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    token_usage_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_category: Mapped[str | None] = mapped_column(String(50), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    trace_json: Mapped[str | None] = mapped_column(Text, nullable=True)

    run: Mapped["EvaluationRunModel"] = relationship(
        "EvaluationRunModel", back_populates="case_results"
    )
    metric_results: Mapped[list["MetricResultModel"]] = relationship(
        "MetricResultModel", back_populates="case_result", cascade="all, delete-orphan"
    )


class MetricResultModel(Base):
    """SQLAlchemy model for single metric evaluation results."""

    __tablename__ = "metric_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    case_result_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("case_results.id", ondelete="CASCADE"), index=True
    )
    run_id: Mapped[str] = mapped_column(String(100), index=True)
    metric_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    metric_name: Mapped[str] = mapped_column(String(255), nullable=False)
    score: Mapped[float | None] = mapped_column(Float, nullable=True)
    passed: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    details_json: Mapped[str] = mapped_column(Text, default="{}")
    is_model_based: Mapped[bool] = mapped_column(Boolean, default=False)

    case_result: Mapped["CaseResultModel"] = relationship(
        "CaseResultModel", back_populates="metric_results"
    )


class RunComparisonModel(Base):
    """SQLAlchemy model for comparing two evaluation runs."""

    __tablename__ = "run_comparisons"

    comparison_id: Mapped[str] = mapped_column(String(100), primary_key=True)
    baseline_run_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    candidate_run_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    delta_metrics_json: Mapped[str] = mapped_column(Text, nullable=False)
    regressions_json: Mapped[str] = mapped_column(Text, default="[]")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
