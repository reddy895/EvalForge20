"""SQLAlchemy ORM models for evaluation runs, case results, and hardware profiles."""

from datetime import datetime

from backend.app.db.database import Base
from sqlalchemy import JSON, Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship


class EvaluationRunORM(Base):
    __tablename__ = "evaluation_runs"

    id = Column(String(64), primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    model_identifier = Column(String(128), nullable=False, index=True)
    provider = Column(String(64), nullable=False)
    task_id = Column(String(64), nullable=False, index=True)
    status = Column(String(32), default="pending", nullable=False)
    total_cases = Column(Integer, default=0)
    completed_cases = Column(Integer, default=0)
    failed_cases = Column(Integer, default=0)
    pass_rate = Column(Float, nullable=True)
    mean_latency_ms = Column(Float, nullable=True)
    aggregates_json = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)

    results = relationship("CaseResultORM", back_populates="run", cascade="all, delete-orphan")


class CaseResultORM(Base):
    __tablename__ = "evaluation_case_results"

    id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(String(64), ForeignKey("evaluation_runs.id"), nullable=False, index=True)
    case_id = Column(String(128), nullable=False)
    prompt = Column(Text, nullable=False)
    expected_output = Column(Text, nullable=True)
    actual_output = Column(Text, nullable=True)
    passed = Column(Boolean, default=False)
    latency_ms = Column(Float, default=0.0)
    error_message = Column(Text, nullable=True)
    error_category = Column(String(64), nullable=True)
    metrics_json = Column(JSON, nullable=True)

    run = relationship("EvaluationRunORM", back_populates="results")


class HardwareProfileORM(Base):
    __tablename__ = "hardware_profiles"

    id = Column(String(64), primary_key=True, index=True)
    os_name = Column(String(64), nullable=False)
    total_ram_gb = Column(Float, nullable=False)
    has_gpu = Column(Boolean, default=False)
    gpu_name = Column(String(128), nullable=True)
    vram_gb = Column(Float, nullable=True)
    disk_space_gb = Column(Float, default=20.0)
    preferred_tradeoff = Column(String(32), default="balanced")
    created_at = Column(DateTime, default=datetime.utcnow)
