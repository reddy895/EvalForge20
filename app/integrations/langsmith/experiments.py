"""LangSmith experiment synchronization logging row-level scores and aggregate benchmarks."""

from typing import Any

from app.domain.results import AggregateMetrics, CaseResult
from app.integrations.langsmith.client import get_langsmith_client
from app.logging import get_logger
from app.runner.config import EvaluationRunRecord

logger = get_logger("evalforge20.integrations.langsmith.experiments")


def sync_run_to_langsmith(
    record: EvaluationRunRecord,
    case_results: list[CaseResult],
    aggregates: AggregateMetrics,
) -> dict[str, Any]:
    """Publish an evaluation run and its evaluator metrics to LangSmith as an experiment.

    Gracefully skips and returns status if LangSmith is disabled.
    """
    client = get_langsmith_client()
    if not client:
        return {
            "status": "skipped",
            "reason": "LangSmith integration is disabled or unconfigured.",
        }

    logger.info("Publishing experiment '%s' (%s) to LangSmith...", record.name, record.run_id)

    try:
        project_name = record.config.name or "evalforge20-experiments"

        # Record parent run trace in LangSmith
        parent_run = client.create_run(
            name=f"eval_{record.name}",
            run_type="chain",
            inputs={
                "dataset_version_hash": record.config.dataset_version_hash,
                "target_model": record.config.target.model_identifier,
                "provider": record.config.target.provider_name,
                "total_cases": record.total_cases,
            },
            outputs={
                "pass_rate": aggregates.pass_rate,
                "completed_cases": record.completed_cases,
                "failed_cases": record.failed_cases,
                "mean_latency_ms": aggregates.mean_latency_ms,
                "metric_averages": aggregates.metric_averages,
            },
            project_name=project_name,
            extra={
                "metadata": {
                    "evalforge20_run_id": record.run_id,
                    "target": record.config.target.model_dump(),
                }
            },
        )

        parent_id = str(parent_run.id)

        # Log row-level metrics as feedback or child steps
        logged_cases = 0
        for case in case_results:
            child_run = client.create_run(
                name=f"case_{case.case_id}",
                run_type="llm",
                parent_run_id=parent_id,
                inputs={"input": case.input},
                outputs={"output": case.actual_output} if case.actual_output is not None else None,
                error=case.error_message,
                project_name=project_name,
                extra={"metadata": {"case_id": case.case_id, "latency_ms": case.latency_ms}},
            )
            # Attach metric scores
            for m in case.metrics:
                if m.score is not None:
                    try:
                        client.create_feedback(
                            run_id=child_run.id,
                            key=m.metric_id,
                            score=m.score,
                            comment=m.reason,
                        )
                    except Exception:
                        pass
            logged_cases += 1

        return {
            "status": "success",
            "langsmith_run_id": parent_id,
            "project_name": project_name,
            "logged_cases": logged_cases,
        }

    except Exception as exc:
        logger.error("Failed to publish experiment to LangSmith: %s", exc)
        return {
            "status": "failed",
            "error": str(exc),
        }
