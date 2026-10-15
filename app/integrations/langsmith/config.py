"""LangSmith integration configuration and status diagnostic models."""

from pydantic import BaseModel, ConfigDict, Field

from app.config import get_settings


class LangSmithStatus(BaseModel):
    """Diagnostic status of optional LangSmith integration."""

    model_config = ConfigDict(frozen=True)

    is_enabled: bool = Field(..., description="True only if tracing enabled and key provided")
    has_api_key: bool = Field(..., description="True if an API key is configured")
    endpoint: str = Field(...)
    project: str = Field(...)
    auto_sync_datasets: bool = Field(...)
    connection_status: str = Field(..., description="disabled, not_configured, reachable, or unreachable")
    error_message: str | None = Field(default=None)


def get_langsmith_status() -> LangSmithStatus:
    """Evaluate and return current LangSmith integration status without remote network calls."""
    settings = get_settings()
    has_key = bool(
        settings.langsmith_api_key and settings.langsmith_api_key.get_secret_value().strip()
    )
    is_enabled = settings.is_langsmith_enabled

    conn_status = "disabled"
    if not settings.langsmith_tracing:
        conn_status = "disabled"
    elif not has_key:
        conn_status = "not_configured"
    else:
        conn_status = "configured"

    return LangSmithStatus(
        is_enabled=is_enabled,
        has_api_key=has_key,
        endpoint=settings.langsmith_endpoint,
        project=settings.langsmith_project,
        auto_sync_datasets=settings.langsmith_auto_sync_datasets,
        connection_status=conn_status,
    )
