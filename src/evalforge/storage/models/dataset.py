"""Dataset and TestCase SQLAlchemy ORM models."""

import json
from typing import Any, Dict, List, Optional
from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.evalforge.storage.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Dataset(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "datasets"

    name: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    tags_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    test_cases: Mapped[List["TestCase"]] = relationship(
        "TestCase",
        back_populates="dataset",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="TestCase.created_at",
    )

    @property
    def tags(self) -> List[str]:
        if not self.tags_json:
            return []
        try:
            return json.loads(self.tags_json)
        except Exception:
            return []

    @tags.setter
    def tags(self, value: List[str]) -> None:
        self.tags_json = json.dumps(value)


class TestCase(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "test_cases"

    dataset_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("datasets.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    expected_output: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    context: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    tags_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    metadata_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    evaluator_config_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    dataset: Mapped["Dataset"] = relationship("Dataset", back_populates="test_cases")

    @property
    def tags(self) -> List[str]:
        if not self.tags_json:
            return []
        try:
            return json.loads(self.tags_json)
        except Exception:
            return []

    @tags.setter
    def tags(self, value: List[str]) -> None:
        self.tags_json = json.dumps(value)

    @property
    def metadata_dict(self) -> Dict[str, Any]:
        if not self.metadata_json:
            return {}
        try:
            return json.loads(self.metadata_json)
        except Exception:
            return {}

    @metadata_dict.setter
    def metadata_dict(self, value: Dict[str, Any]) -> None:
        self.metadata_json = json.dumps(value)

    @property
    def evaluator_config(self) -> Dict[str, Any]:
        if not self.evaluator_config_json:
            return {}
        try:
            return json.loads(self.evaluator_config_json)
        except Exception:
            return {}

    @evaluator_config.setter
    def evaluator_config(self, value: Dict[str, Any]) -> None:
        self.evaluator_config_json = json.dumps(value)
