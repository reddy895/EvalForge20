"""Non-blocking, optional LangSmith tracing adapter with sensitive prompt redaction."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

from app.config import get_settings
from app.integrations.langsmith.client import get_langsmith_client
from app.logging import get_logger

logger = get_logger("evalforge20.integrations.langsmith")


@asynccontextmanager
async def trace_evaluation_run(
    run_name: str,
    run_id: str,
    metadata: dict[str, Any] | None = None,
) -> AsyncGenerator[dict[str, Any], None]:
    """Context manager for tracing an evaluation run in LangSmith when enabled.

    Does nothing and executes zero network requests when LangSmith is disabled.
    """
    settings = get_settings()
    if not settings.is_langsmith_enabled:
        # Non-blocking no-op
        yield {"run_id": run_id, "traced": False}
        return

    client = get_langsmith_client()
    if not client:
        yield {"run_id": run_id, "traced": False}
        return

    run_meta = metadata or {}
    run_meta.update({"evalforge20_run_id": run_id, "project": settings.langsmith_project})

    try:
        from langsmith import trace

        with trace(
            name=run_name,
            run_type="chain",
            metadata=run_meta,
            project_name=settings.langsmith_project,
        ) as rt:
            yield {"run_id": run_id, "traced": True, "trace_tree": rt}
    except Exception as exc:
        logger.warning(
            "LangSmith tracing encountered error: %s (local execution continues unaffected)", exc
        )
        yield {"run_id": run_id, "traced": False, "error": str(exc)}


def record_case_trace(
    run_id: str,
    case_id: str,
    inputs: Any,
    outputs: Any,
    latency_ms: float | None = None,
    error: str | None = None,
    tokens: dict[str, int] | None = None,
) -> None:
    """Record an individual case step trace to LangSmith if tracing is active."""
    settings = get_settings()
    if not settings.is_langsmith_enabled:
        return

    client = get_langsmith_client()
    if not client:
        return

    # Redact prompts if log_prompts is disabled
    safe_inputs = inputs if settings.log_prompts else {"case_id": case_id, "redacted": True}
    safe_outputs = outputs if settings.log_prompts else {"redacted": True}

    try:
        client.create_run(
            name=f"case_{case_id}",
            run_type="llm",
            inputs={"input": safe_inputs},
            outputs={"output": safe_outputs} if not error else None,
            error=error,
            project_name=settings.langsmith_project,
            extra={
                "metadata": {
                    "evalforge20_run_id": run_id,
                    "case_id": case_id,
                    "latency_ms": latency_ms,
                    "token_usage": tokens,
                }
            },
        )
    except Exception as exc:
        logger.debug("Failed to record individual case trace to LangSmith: %s", exc)
