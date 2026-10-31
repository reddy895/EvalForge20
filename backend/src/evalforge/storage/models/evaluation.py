"""EvaluationRun and CaseResult SQLAlchemy ORM models."""

import json
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.evalforge.storage.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class EvaluationRun(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "evaluation_runs"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    model_id: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    provider: Mapped[str] = mapped_column(String(64), nullable=False, default="ollama")
    dataset_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("datasets.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    dataset_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(String(32), index=True, default="queued", nullable=False)
    config_json: Mapped[str | None] = mapped_column(Text, nullable=True)

    total_cases: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    completed_cases: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    passed_cases: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    failed_cases: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    pass_rate: Mapped[float | None] = mapped_column(Float, nullable=True)
    avg_latency_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    summary_metrics_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    results: Mapped[list["CaseResult"]] = relationship(
        "CaseResult",
        back_populates="evaluation_run",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="CaseResult.created_at",
    )

    @property
    def case_results(self) -> list["CaseResult"]:
        return self.results

    @property
    def config(self) -> dict[str, Any]:
        if not self.config_json:
            return {}
        try:
            return json.loads(self.config_json)
        except Exception:
            return {}

    @config.setter
    def config(self, value: dict[str, Any]) -> None:
        self.config_json = json.dumps(value)

    @property
    def summary_metrics(self) -> dict[str, Any]:
        if not self.summary_metrics_json:
            return {}
        try:
            return json.loads(self.summary_metrics_json)
        except Exception:
            return {}

    @summary_metrics.setter
    def summary_metrics(self, value: dict[str, Any]) -> None:
        self.summary_metrics_json = json.dumps(value)


class CaseResult(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "case_results"

    evaluation_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("evaluation_runs.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    case_id: Mapped[str] = mapped_column(String(36), index=True, nullable=False)
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    expected_output: Mapped[str | None] = mapped_column(Text, nullable=True)
    actual_output: Mapped[str | None] = mapped_column(Text, nullable=True)
    passed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    latency_ms: Mapped[float | None] = mapped_column(Float, nullable=True, default=None)
    token_usage_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    metrics_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        server_default=func.now(),
        nullable=False,
    )

    evaluation_run: Mapped["EvaluationRun"] = relationship(
        "EvaluationRun", back_populates="results"
    )

    @property
    def metrics(self) -> dict[str, Any]:
        if not self.metrics_json:
            return {}
        try:
            return json.loads(self.metrics_json)
        except Exception:
            return {}

    @metrics.setter
    def metrics(self, value: dict[str, Any]) -> None:
        self.metrics_json = json.dumps(value)

    @property
    def token_usage(self) -> dict[str, Any]:
        if not self.token_usage_json:
            return {}
        try:
            return json.loads(self.token_usage_json)
        except Exception:
            return {}

    @token_usage.setter
    def token_usage(self, value: dict[str, Any]) -> None:
        self.token_usage_json = json.dumps(value)
