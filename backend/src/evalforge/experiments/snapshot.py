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

    for idx, case in enumerate(dataset.test_cases):
        case_id = str(getattr(case, "id", None) or f"case-{idx}")
        raw_prompt = getattr(case, "prompt", None)
        prompt_str = str(raw_prompt) if raw_prompt is not None else ""
        raw_expected = getattr(case, "expected_output", None)
        expected_str = str(raw_expected) if raw_expected is not None else None
        context_str = str(case.context) if getattr(case, "context", None) is not None else None

        frozen = FrozenTestCase(
            id=case_id,
            prompt=prompt_str,
            expected_output=expected_str,
            context=context_str,
            tags=getattr(case, "tags", []) or [],
            metadata=getattr(case, "metadata_dict", {}) or {},
            evaluator_config=getattr(case, "evaluator_config", {}) or {},
        )
        frozen_cases.append(frozen)

        # Include prompt and reference in content hash safely
        hasher.update(case_id.encode("utf-8"))
        hasher.update(prompt_str.encode("utf-8"))
        if expected_str:
            hasher.update(expected_str.encode("utf-8"))

    snapshot_hash = hasher.hexdigest()

    return DatasetSnapshot(
        dataset_id=ds_id,
        dataset_name=dataset.name,
        version=dataset.version,
        snapshot_hash=snapshot_hash,
        total_cases=len(frozen_cases),
        cases=frozen_cases,
    )


class ExperimentSnapshot(BaseModel):
    """Complete freeze-frame of experiment configuration, models, evaluators, and hardware."""

    experiment_id: str
    workflow_id: str | None = None
    model_identifier: str
    model_version: str | None = None
    hardware_specs: dict[str, Any]
    evaluator_names: list[str]
    generation_parameters: dict[str, Any]
    snapshot_timestamp: str


__all__ = [
    "FrozenTestCase",
    "DatasetSnapshot",
    "create_dataset_snapshot",
    "ExperimentSnapshot",
]
