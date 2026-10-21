"""Dataset snapshot builder for freeze-state reproducibility."""

import hashlib
from typing import Any

from pydantic import BaseModel, Field

from src.evalforge.storage.models.dataset import Dataset


class FrozenTestCase(BaseModel):
    __test__ = False
    id: str
    prompt: str
    expected_output: str | None = None
    context: str | None = None
    tags: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    evaluator_config: dict[str, Any] = Field(default_factory=dict)


class DatasetSnapshot(BaseModel):
    dataset_id: str
    dataset_name: str
    version: int
    snapshot_hash: str
    total_cases: int
    cases: list[FrozenTestCase]


def create_dataset_snapshot(dataset: Dataset) -> DatasetSnapshot:
    """Create an immutable, serializable snapshot of test cases with a cryptographic digest."""
    frozen_cases: list[FrozenTestCase] = []

    ds_id = str(dataset.id or "transient")
    hasher = hashlib.sha256()
    hasher.update(f"{ds_id}:{dataset.name}:{dataset.version}".encode())

    for case in dataset.test_cases:
        frozen = FrozenTestCase(
            id=case.id,
            prompt=case.prompt,
            expected_output=case.expected_output,
            context=case.context,
            tags=case.tags,
            metadata=case.metadata_dict,
            evaluator_config=case.evaluator_config,
        )
        frozen_cases.append(frozen)

        # Include prompt and reference in content hash
        hasher.update(case.id.encode("utf-8"))
        hasher.update(case.prompt.encode("utf-8"))
        if case.expected_output:
            hasher.update(case.expected_output.encode("utf-8"))

    snapshot_hash = hasher.hexdigest()

    return DatasetSnapshot(
        dataset_id=ds_id,
        dataset_name=dataset.name,
        version=dataset.version,
        snapshot_hash=snapshot_hash,
        total_cases=len(frozen_cases),
        cases=frozen_cases,
    )
