"""Dataset snapshot builder for freeze-state reproducibility."""

import hashlib
import json
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from src.evalforge.storage.models.dataset import Dataset


class FrozenTestCase(BaseModel):
    __test__ = False
    id: str
    prompt: str
    expected_output: Optional[str] = None
    context: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    evaluator_config: Dict[str, Any] = Field(default_factory=dict)


class DatasetSnapshot(BaseModel):
    dataset_id: str
    dataset_name: str
    version: int
    snapshot_hash: str
    total_cases: int
    cases: List[FrozenTestCase]


def create_dataset_snapshot(dataset: Dataset) -> DatasetSnapshot:
    """Create an immutable, serializable snapshot of test cases with a cryptographic digest."""
    frozen_cases: List[FrozenTestCase] = []

    hasher = hashlib.sha256()
    hasher.update(f"{dataset.id}:{dataset.name}:{dataset.version}".encode("utf-8"))

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
        dataset_id=dataset.id,
        dataset_name=dataset.name,
        version=dataset.version,
        snapshot_hash=snapshot_hash,
        total_cases=len(frozen_cases),
        cases=frozen_cases,
    )
