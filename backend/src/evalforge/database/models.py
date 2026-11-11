"""SQLAlchemy database models for EvalForge20."""

import uuid
from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.evalforge.storage.base import Base, TimestampMixin

# Import existing models for unified registry
from src.evalforge.storage.models.benchmark import BenchmarkComparison as BenchmarkRecord
from src.evalforge.storage.models.dataset import Dataset as DatasetRecord
from src.evalforge.storage.models.dataset import TestCase as DatasetCaseRecord
from src.evalforge.storage.models.evaluation import CaseResult as CaseResultRecord
from src.evalforge.storage.models.evaluation import EvaluationRun as EvaluationRunRecord
from src.evalforge.storage.models.provider import ProviderRecord, RegisteredModelRecord


class WorkflowRecord(Base, TimestampMixin):
    """Stores visual node canvas workflows created in the Playground."""

    __tablename__ = "workflows"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False, default="Untitled Workflow")
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    graph_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    executions: Mapped[list["ExecutionRecord"]] = relationship(
        "ExecutionRecord",
        back_populates="workflow",
        cascade="all, delete-orphan",
    )


class ExecutionRecord(Base):
    """Tracks a live or completed workflow execution run."""

    __tablename__ = "workflow_executions"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        nullable=False,
    )
    workflow_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("workflows.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    status: Mapped[str] = mapped_column(
        String(32),
        default="PENDING",
        nullable=False,
        index=True,
    )
    total_steps: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    completed_steps: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    logs_json: Mapped[str] = mapped_column(Text, default="[]", nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    workflow: Mapped[WorkflowRecord | None] = relationship("WorkflowRecord", back_populates="executions")


class ExperimentRecord(Base, TimestampMixin):
    """Historical experiment record capturing full evaluation results and hardware metadata."""

    __tablename__ = "experiments"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    workflow_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    execution_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    model_identifier: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    dataset_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    evaluator_ids_json: Mapped[str] = mapped_column(Text, default="[]", nullable=False)
    metrics_json: Mapped[str] = mapped_column(Text, default="{}", nullable=False)
    parameters_json: Mapped[str] = mapped_column(Text, default="{}", nullable=False)
    hardware_json: Mapped[str] = mapped_column(Text, default="{}", nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="COMPLETED", nullable=False)


__all__ = [
    "Base",
    "WorkflowRecord",
    "ExecutionRecord",
    "ExperimentRecord",
    "EvaluationRunRecord",
    "CaseResultRecord",
    "DatasetRecord",
    "DatasetCaseRecord",
    "BenchmarkRecord",
    "ProviderRecord",
    "RegisteredModelRecord",
]
