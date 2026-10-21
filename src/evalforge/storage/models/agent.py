"""AgentEvaluation and AgentTrace SQLAlchemy ORM models."""

import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.evalforge.storage.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class AgentEvaluation(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "agent_evaluations"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    model_id: Mapped[str] = mapped_column(String(255), nullable=False)
    provider: Mapped[str] = mapped_column(String(64), nullable=False, default="ollama")
    task: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="queued", nullable=False)
    total_steps: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    max_steps: Mapped[int] = mapped_column(Integer, default=10, nullable=False)
    task_completed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    tool_accuracy: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    schema_validity: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    policy_violations: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    final_output: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    traces: Mapped[List["AgentTrace"]] = relationship(
        "AgentTrace",
        back_populates="agent_evaluation",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="AgentTrace.step_number",
    )


class AgentTrace(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "agent_traces"

    evaluation_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("agent_evaluations.id", ondelete="CASCADE"),
        nullable=False,
    )
    step_number: Mapped[int] = mapped_column(Integer, nullable=False)
    tool_name: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    tool_args_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    tool_result_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    thought: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    duration_ms: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    is_valid_call: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
    )

    agent_evaluation: Mapped["AgentEvaluation"] = relationship(
        "AgentEvaluation", back_populates="traces"
    )

    @property
    def tool_args(self) -> Dict[str, Any]:
        if not self.tool_args_json:
            return {}
        try:
            return json.loads(self.tool_args_json)
        except Exception:
            return {}

    @tool_args.setter
    def tool_args(self, value: Dict[str, Any]) -> None:
        self.tool_args_json = json.dumps(value)

    @property
    def tool_result(self) -> Any:
        if not self.tool_result_json:
            return None
        try:
            return json.loads(self.tool_result_json)
        except Exception:
            return self.tool_result_json

    @tool_result.setter
    def tool_result(self, value: Any) -> None:
        if isinstance(value, (dict, list)):
            self.tool_result_json = json.dumps(value)
        else:
            self.tool_result_json = str(value)
