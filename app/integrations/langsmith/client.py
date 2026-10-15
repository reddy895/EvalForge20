"""LangSmith client creation and connectivity verification."""

from typing import Any

import httpx

from app.config import get_settings
from app.integrations.langsmith.config import LangSmithStatus, get_langsmith_status


def get_langsmith_client() -> Any | None:
    """Return an authenticated LangSmith client if configured, else None."""
    settings = get_settings()
    if not settings.is_langsmith_enabled:
        return None

    try:
        from langsmith import Client

        key = settings.langsmith_api_key.get_secret_value() if settings.langsmith_api_key else None
        return Client(
            api_url=settings.langsmith_endpoint,
            api_key=key,
        )
    except Exception:
        return None


async def check_langsmith_connection() -> LangSmithStatus:
    """Perform network diagnostic check against configured LangSmith endpoint."""
    status_base = get_langsmith_status()
    if not status_base.is_enabled:
        return status_base

    settings = get_settings()
    key = settings.langsmith_api_key.get_secret_value() if settings.langsmith_api_key else ""
    endpoint = settings.langsmith_endpoint.rstrip("/")

    try:
        async with httpx.AsyncClient(timeout=4.0) as client:
            resp = await client.get(
                f"{endpoint}/info",
                headers={"x-api-key": key},
            )
            if resp.status_code in (200, 401, 403):
                if resp.status_code == 200:
                    conn_status = "reachable"
                    err = None
                else:
                    conn_status = "unreachable"
                    err = f"Authentication rejected with HTTP {resp.status_code}"
            else:
                conn_status = "unreachable"
                err = f"Unexpected response code: HTTP {resp.status_code}"
    except Exception as exc:
        conn_status = "unreachable"
        err = f"Connection failed: {exc}"

    return LangSmithStatus(
        is_enabled=status_base.is_enabled,
        has_api_key=status_base.has_api_key,
        endpoint=status_base.endpoint,
        project=status_base.project,
        auto_sync_datasets=status_base.auto_sync_datasets,
        connection_status=conn_status,
        error_message=err,
    )
