"""SQLAlchemy engine, session factory, and connection initialization."""

from collections.abc import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import get_settings


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy ORM models."""

    pass


def get_engine(db_url: str | None = None):
    """Create and return a SQLAlchemy engine with SQLite pragmas enabled."""
    url = db_url or get_settings().database_url
    connect_args = {}
    if url.startswith("sqlite"):
        connect_args["check_same_thread"] = False
    return create_engine(url, connect_args=connect_args)


def get_session_factory(engine=None):
    """Create a configured sessionmaker."""
    eng = engine or get_engine()
    return sessionmaker(autocommit=False, autoflush=False, bind=eng)


def init_db(engine=None) -> None:
    """Create all database tables if they do not already exist."""
    eng = engine or get_engine()
    Base.metadata.create_all(bind=eng)


def get_db() -> Generator[Session, None, None]:
    """Dependency yield for FastAPI request lifecycle and transactional sessions."""
    engine = get_engine()
    session_factory = get_session_factory(engine)
    session = session_factory()
    try:
        yield session
    finally:
        session.close()
