"""External service integration endpoints."""

from fastapi import APIRouter

from app.integrations.langsmith.client import check_langsmith_connection
from app.integrations.langsmith.config import LangSmithStatus

integrations_router = APIRouter(prefix="/v1/integrations", tags=["Integrations"])


@integrations_router.get(
    "/langsmith/status",
    response_model=LangSmithStatus,
    summary="Check LangSmith integration status and connectivity",
)
async def get_langsmith_status_endpoint() -> LangSmithStatus:
    """Return current configuration and network diagnostics for LangSmith."""
    return await check_langsmith_connection()
