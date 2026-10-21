"""Application configuration using Pydantic Settings."""

from functools import lru_cache
from typing import List
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    APP_NAME: str = "EvalForge20"
    APP_VERSION: str = "2.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"

    # Server binding (defaults to localhost for security)
    HOST: str = "127.0.0.1"
    PORT: int = 8000

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./evalforge.db"
    DATABASE_ECHO: bool = False

    # Ollama Provider
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_TIMEOUT_SECONDS: float = 60.0

    # Concurrency and Limits
    DEFAULT_CONCURRENCY_LIMIT: int = 4
    MAX_CONCURRENCY_LIMIT: int = 16
    MAX_DATASET_FILE_SIZE_BYTES: int = 10 * 1024 * 1024  # 10MB
    MAX_CASES_PER_DATASET: int = 2000

    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
    ]

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"  # "json" or "console"

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: object) -> List[str]:
        if isinstance(v, str):
            return [i.strip() for i in v.split(",") if i.strip()]
        if isinstance(v, list):
            return v
        return ["http://localhost:5173", "http://127.0.0.1:5173"]


@lru_cache
def get_settings() -> Settings:
    """Return cached application settings instance."""
    return Settings()
