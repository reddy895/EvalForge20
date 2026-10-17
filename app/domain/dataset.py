"""Dataset and dataset-version domain models with multi-format parsing and stats computation."""

import csv
import hashlib
import io
import json
from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.domain.models import EvaluationCase


class DatasetStats(BaseModel):
    """Aggregate statistics for a dataset version."""

    model_config = ConfigDict(frozen=True)

    total_cases: int = Field(default=0, ge=0)
    cases_with_expected_output: int = Field(default=0, ge=0)
    categories_distribution: dict[str, int] = Field(default_factory=dict)
    tags_distribution: dict[str, int] = Field(default_factory=dict)
    complexity_distribution: dict[str, int] = Field(default_factory=dict)
    has_context_count: int = Field(default=0, ge=0)
    has_tools_count: int = Field(default=0, ge=0)

    @classmethod
    def from_cases(cls, cases: list[EvaluationCase]) -> "DatasetStats":
        """Compute aggregate statistics from a list of evaluation cases."""
        total = len(cases)
        with_expected = sum(1 for c in cases if c.expected_output is not None)
        cats: dict[str, int] = {}
        tags: dict[str, int] = {}
        complexities: dict[str, int] = {}
        has_ctx = 0
        has_tools = 0

        for c in cases:
            if c.category:
                cats[c.category] = cats.get(c.category, 0) + 1
            for t in c.tags:
                tags[t] = tags.get(t, 0) + 1

            # Extract complexity band from metadata if present
            comp = c.metadata.get("complexity") or c.metadata.get("difficulty")
            if comp:
                comp_str = str(comp).lower()
                complexities[comp_str] = complexities.get(comp_str, 0) + 1

            if c.context:
                has_ctx += 1
            if c.tools:
                has_tools += 1

        return cls(
            total_cases=total,
            cases_with_expected_output=with_expected,
            categories_distribution=cats,
            tags_distribution=tags,
            complexity_distribution=complexities,
            has_context_count=has_ctx,
            has_tools_count=has_tools,
        )


class DatasetVersion(BaseModel):
    """An immutable versioned snapshot of an evaluation dataset."""

    model_config = ConfigDict(frozen=True)

    version_id: str = Field(..., description="Unique version identifier")
    dataset_id: str = Field(..., description="Parent dataset identifier")
    version_number: int = Field(default=1, ge=1)
    content_hash: str = Field(..., description="SHA-256 hash of dataset cases")
    cases: list[EvaluationCase] = Field(default_factory=list)
    stats: DatasetStats = Field(default_factory=DatasetStats)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @classmethod
    def create(
        cls,
        dataset_id: str,
        cases: list[EvaluationCase],
        version_number: int = 1,
    ) -> "DatasetVersion":
        """Construct a validated DatasetVersion with computed content hash and stats."""
        # Canonical hash of cases
        serialized = json.dumps([c.model_dump() for c in cases], sort_keys=True)
        content_hash = hashlib.sha256(serialized.encode("utf-8")).hexdigest()
        version_id = f"{dataset_id}-v{version_number}-{content_hash[:8]}"
        stats = DatasetStats.from_cases(cases)

        return cls(
            version_id=version_id,
            dataset_id=dataset_id,
            version_number=version_number,
            content_hash=content_hash,
            cases=cases,
            stats=stats,
        )

    @classmethod
    def from_jsonl_content(cls, dataset_id: str, content: str) -> "DatasetVersion":
        """Parse raw JSONL text into a validated DatasetVersion."""
        cases: list[EvaluationCase] = []
        for line_num, line in enumerate(content.splitlines(), start=1):
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            data = json.loads(stripped)
            if "id" not in data:
                data["id"] = f"case_{line_num}"
            cases.append(EvaluationCase.model_validate(data))
        return cls.create(dataset_id=dataset_id, cases=cases)

    @classmethod
    def from_json_content(cls, dataset_id: str, content: str) -> "DatasetVersion":
        """Parse raw JSON text (array of cases or object with cases key) into a DatasetVersion."""
        data = json.loads(content)
        items = data.get("cases", data) if isinstance(data, dict) else data
        if not isinstance(items, list):
            raise ValueError("Expected JSON array of evaluation cases")

        cases: list[EvaluationCase] = []
        for idx, item in enumerate(items, start=1):
            if "id" not in item:
                item["id"] = f"case_{idx}"
            cases.append(EvaluationCase.model_validate(item))
        return cls.create(dataset_id=dataset_id, cases=cases)

    @classmethod
    def from_csv_content(cls, dataset_id: str, content: str) -> "DatasetVersion":
        """Parse raw CSV text into a DatasetVersion."""
        reader = csv.DictReader(io.StringIO(content))
        cases: list[EvaluationCase] = []
        for idx, row in enumerate(reader, start=1):
            case_id = row.get("id") or str(idx)
            input_val = row.get("input") or row.get("prompt") or ""
            expected = row.get("expected_output") or row.get("target") or row.get("label")
            category = row.get("category")
            tags = [t.strip() for t in row.get("tags", "").split(",") if t.strip()]
            complexity = row.get("complexity")

            metadata: dict[str, Any] = {}
            if complexity:
                metadata["complexity"] = complexity

            cases.append(
                EvaluationCase(
                    id=case_id,
                    input=input_val,
                    expected_output=expected,
                    category=category,
                    tags=tags,
                    metadata=metadata,
                )
            )
        return cls.create(dataset_id=dataset_id, cases=cases)


class Dataset(BaseModel):
    """A logical dataset grouping multiple versions."""

    model_config = ConfigDict(frozen=True)

    id: str = Field(..., min_length=1, description="Unique slug or ID of dataset")
    name: str = Field(..., min_length=1, description="Human readable dataset name")
    description: str | None = Field(default=None)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    latest_version: int = Field(default=1, ge=1)
