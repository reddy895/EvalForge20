"""Database engine configuration and async session management."""

from collections.abc import AsyncGenerator
from typing import Any

from sqlalchemy import event
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from src.evalforge.core.config import get_settings
from src.evalforge.core.logging import get_logger

logger = get_logger("evalforge.database")

_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def get_engine() -> AsyncEngine:
    global _engine
    if _engine is None:
        settings = get_settings()
        connect_args = {}
        if "sqlite" in settings.DATABASE_URL:
            # Enable SQLite write-ahead logging and multi-threaded check_same_thread
            connect_args = {"check_same_thread": False}

        _engine = create_async_engine(
            settings.DATABASE_URL,
            echo=settings.DATABASE_ECHO,
            future=True,
            connect_args=connect_args,
        )

        # Enforce foreign key constraints in SQLite
        if "sqlite" in settings.DATABASE_URL:

            @event.listens_for(_engine.sync_engine, "connect")
            def set_sqlite_pragma(dbapi_connection: object, _: object) -> None:
                cursor = dbapi_connection.cursor()  # type: ignore[attr-defined]
                cursor.execute("PRAGMA foreign_keys=ON")
                cursor.execute("PRAGMA journal_mode=WAL")
                cursor.close()

    return _engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    global _session_factory
    if _session_factory is None:
        engine = get_engine()
        _session_factory = async_sessionmaker(
            bind=engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
        )
    return _session_factory


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency yielding an async database session within a transaction context."""
    session_factory = get_session_factory()
    async with session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def init_db() -> None:
    """Initialize database tables for development/testing if migrations have not run."""
    # Import all models so metadata knows all tables
    import src.evalforge.storage.models  # noqa: F401
    from src.evalforge.storage.base import Base

    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

        def _check_and_migrate_sqlite(sync_conn: Any) -> None:
            try:
                info = sync_conn.exec_driver_sql("PRAGMA table_info(case_results);").fetchall()
                latency_col = next((c for c in info if c[1] == "latency_ms"), None)
                if latency_col and latency_col[3] == 1:
                    sync_conn.exec_driver_sql("PRAGMA foreign_keys=OFF;")
                    sync_conn.exec_driver_sql("""
                        CREATE TABLE case_results_new (
                            evaluation_id VARCHAR(36) NOT NULL,
                            case_id VARCHAR(36) NOT NULL,
                            prompt TEXT NOT NULL,
                            expected_output TEXT,
                            actual_output TEXT,
                            passed BOOLEAN NOT NULL,
                            latency_ms FLOAT,
                            token_usage_json TEXT,
                            metrics_json TEXT,
                            error_message TEXT,
                            created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
                            id VARCHAR(36) NOT NULL,
                            PRIMARY KEY (id),
                            FOREIGN KEY(evaluation_id) REFERENCES evaluation_runs (id) ON DELETE CASCADE
                        );
                    """)
                    sync_conn.exec_driver_sql("""
                        INSERT INTO case_results_new SELECT evaluation_id, case_id, prompt, expected_output, actual_output, passed, latency_ms, token_usage_json, metrics_json, error_message, created_at, id FROM case_results;
                    """)
                    sync_conn.exec_driver_sql("DROP TABLE case_results;")
                    sync_conn.exec_driver_sql("ALTER TABLE case_results_new RENAME TO case_results;")
                    sync_conn.exec_driver_sql("CREATE INDEX IF NOT EXISTS ix_case_results_case_id ON case_results (case_id);")
                    sync_conn.exec_driver_sql("CREATE INDEX IF NOT EXISTS ix_case_results_evaluation_id ON case_results (evaluation_id);")
                    sync_conn.exec_driver_sql("PRAGMA foreign_keys=ON;")
            except Exception:
                pass

        await conn.run_sync(_check_and_migrate_sqlite)
    logger.info("Database schema initialized successfully.")

    # Seed default providers and catalog models if table is empty
    session_factory = get_session_factory()
    async with session_factory() as session:
        import json

        from sqlalchemy import func, select

        from src.evalforge.providers.registry import get_provider_registry
        from src.evalforge.services.model_service import VERIFIED_CATALOG_MODELS
        from src.evalforge.storage.models.provider import ProviderRecord, RegisteredModelRecord

        try:
            cnt = await session.scalar(select(func.count(ProviderRecord.id)))
            if cnt == 0:
                reg = get_provider_registry()
                details = await reg.list_details()
                for p in details:
                    session.add(
                        ProviderRecord(
                            id=p.name,
                            name=p.name,
                            display_name=p.display_name,
                            provider_type=p.provider_type,
                            implementation_status=p.implementation_status,
                            base_url=p.base_url,
                            is_configured=p.is_configured,
                            is_healthy=p.healthy,
                            setup_instructions=p.setup_instructions,
                        )
                    )
                for m in VERIFIED_CATALOG_MODELS:
                    session.add(
                        RegisteredModelRecord(
                            id=m.id,
                            name=m.name,
                            provider_id=m.provider,
                            model_identifier=m.model_identifier or m.id,
                            family=m.family,
                            parameter_count=m.parameter_count,
                            context_window=m.context_window,
                            is_local=m.is_local,
                            is_installed=m.is_installed,
                            supports_tools=m.supports_tools,
                            supports_structured_output=m.supports_structured_output,
                            license=m.license,
                            description=m.description,
                            metadata_json=json.dumps(m.model_dump(), default=str),
                        )
                    )
                await session.commit()
                logger.info("Seeded initial providers and catalog models into database.")

            # Seed standard evaluation datasets if not already present
            from src.evalforge.datasets.seeder import seed_standard_datasets
            await seed_standard_datasets(session)
        except Exception as exc:
            logger.debug("Database seeding skipped or encountered: %s", exc)


async def close_db() -> None:
    """Dispose of engine connection pool gracefully on shutdown."""
    global _engine, _session_factory
    if _engine is not None:
        await _engine.dispose()
        _engine = None
        _session_factory = None
        logger.info("Database engine connections closed.")
