"""Optional dataset synchronization service uploading local datasets to LangSmith."""

from typing import Any

from app.domain.models import EvaluationCase
from app.integrations.langsmith.client import get_langsmith_client
from app.logging import get_logger

logger = get_logger("evalforge20.integrations.langsmith.sync")


def sync_dataset_to_langsmith(
    cases: list[EvaluationCase],
    dataset_name: str,
    description: str | None = None,
) -> dict[str, Any]:
    """Register or synchronize an EvalForge20 dataset with LangSmith.

    Raises:
        ValueError: If LangSmith credentials are not configured or tracing is disabled.
        RuntimeError: If remote LangSmith API call fails.
    """
    client = get_langsmith_client()
    if not client:
        raise ValueError(
            "Cannot synchronize dataset: LangSmith is disabled or API key is not configured. "
            "Set LANGSMITH_TRACING=true and LANGSMITH_API_KEY in environment."
        )

    logger.info("Synchronizing dataset '%s' (%d cases) to LangSmith...", dataset_name, len(cases))

    try:
        # Check if dataset already exists, otherwise create it
        ls_dataset = None
        try:
            ls_dataset = client.read_dataset(dataset_name=dataset_name)
            logger.info("Found existing LangSmith dataset with ID: %s", ls_dataset.id)
        except Exception:
            # Does not exist yet, create new
            ls_dataset = client.create_dataset(
                dataset_name=dataset_name,
                description=description or f"EvalForge20 dataset with {len(cases)} cases",
            )
            logger.info("Created new LangSmith dataset with ID: %s", ls_dataset.id)

        dataset_id = str(ls_dataset.id)

        # Prepare examples
        inputs_list = []
        outputs_list = []
        metadata_list = []

        for c in cases:
            inputs_list.append({"input": c.input})
            outputs_list.append(
                {"expected_output": c.expected_output} if c.expected_output is not None else {}
            )
            metadata_list.append(
                {
                    "case_id": c.id,
                    "category": c.category,
                    "tags": c.tags,
                }
            )

        client.create_examples(
            inputs=inputs_list,
            outputs=outputs_list,
            dataset_id=dataset_id,
            metadata=metadata_list,
        )

        return {
            "dataset_id": dataset_id,
            "dataset_name": dataset_name,
            "synced_examples": len(cases),
            "status": "success",
        }
    except Exception as exc:
        logger.error("Failed to synchronize dataset to LangSmith: %s", exc)
        raise RuntimeError(f"LangSmith dataset synchronization failed: {exc}") from exc
