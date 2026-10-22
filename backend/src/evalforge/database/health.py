"""Database connectivity and schema validation probe."""

from sqlalchemy import text
from src.evalforge.storage.database import get_engine

async def check_database_health() -> dict[str, str | bool | int]:
    """Execute low-overhead probe against configured database engine."""
    engine = get_engine()
    try:
        async with engine.connect() as conn:
            res = await conn.execute(text("SELECT 1"))
            val = res.scalar()
            is_healthy = val == 1
        return {
            "connected": is_healthy,
            "status": "healthy" if is_healthy else "unhealthy",
            "backend": engine.dialect.name,
        }
    except Exception as exc:
        return {
            "connected": False,
            "status": "error",
            "error": str(exc),
            "backend": engine.dialect.name if engine else "unknown",
        }
