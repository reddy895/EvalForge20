"""BenchmarkComparison SQLAlchemy ORM model for multi-model comparisons."""

import json
from typing import Any, Dict, List, Optional
from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.evalforge.storage.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class BenchmarkComparison(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "benchmark_comparisons"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    dataset_id: Mapped[str] = mapped_column(String(36), nullable=False)
    dataset_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    model_ids_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    evaluation_ids_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    summary_matrix_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    reproducibility_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    @property
    def model_ids(self) -> List[str]:
        if not self.model_ids_json:
            return []
        try:
            return json.loads(self.model_ids_json)
        except Exception:
            return []

    @model_ids.setter
    def model_ids(self, value: List[str]) -> None:
        self.model_ids_json = json.dumps(value)

    @property
    def evaluation_ids(self) -> List[str]:
        if not self.evaluation_ids_json:
            return []
        try:
            return json.loads(self.evaluation_ids_json)
        except Exception:
            return []

    @evaluation_ids.setter
    def evaluation_ids(self, value: List[str]) -> None:
        self.evaluation_ids_json = json.dumps(value)

    @property
    def summary_matrix(self) -> Dict[str, Any]:
        if not self.summary_matrix_json:
            return {}
        try:
            return json.loads(self.summary_matrix_json)
        except Exception:
            return {}

    @summary_matrix.setter
    def summary_matrix(self, value: Dict[str, Any]) -> None:
        self.summary_matrix_json = json.dumps(value)

    @property
    def reproducibility(self) -> Dict[str, Any]:
        if not self.reproducibility_json:
            return {}
        try:
            return json.loads(self.reproducibility_json)
        except Exception:
            return {}

    @reproducibility.setter
    def reproducibility(self, value: Dict[str, Any]) -> None:
        self.reproducibility_json = json.dumps(value)
