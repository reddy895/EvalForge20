"""Dataset exporter for streaming JSONL export."""

import json
from collections.abc import Iterator

from src.evalforge.storage.models.dataset import Dataset


def export_dataset_to_jsonl(dataset: Dataset) -> str:
    """Serialize entire dataset and its test cases into a standard JSONL document."""
    lines = []
    for case in dataset.test_cases:
        row = {
            "id": case.id,
            "prompt": case.prompt,
            "expected_output": case.expected_output,
            "context": case.context,
            "tags": case.tags,
            "metadata": case.metadata_dict,
            "evaluator_config": case.evaluator_config,
        }
        lines.append(json.dumps(row, ensure_ascii=False))

    return "\n".join(lines) + ("\n" if lines else "")


def stream_dataset_jsonl(dataset: Dataset) -> Iterator[str]:
    """Generator streaming JSONL rows line-by-line for high efficiency."""
    for case in dataset.test_cases:
        row = {
            "id": case.id,
            "prompt": case.prompt,
            "expected_output": case.expected_output,
            "context": case.context,
            "tags": case.tags,
            "metadata": case.metadata_dict,
            "evaluator_config": case.evaluator_config,
        }
        yield json.dumps(row, ensure_ascii=False) + "\n"
