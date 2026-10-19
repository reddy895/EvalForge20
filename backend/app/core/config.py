"""Configuration management for EvalForge20."""

from functools import lru_cache

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """EvalForge20 environment configuration."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "EvalForge20"
    app_version: str = "2.0.0"
    environment: str = Field(default="development", alias="EVALFORGE20_ENV")

    # Local Ollama Configuration
    ollama_base_url: str = Field(default="http://localhost:11434", alias="OLLAMA_BASE_URL")
    ollama_timeout_seconds: float = Field(default=60.0, alias="OLLAMA_TIMEOUT_SECONDS")

    # Storage
    database_url: str = Field(default="sqlite:///./evalforge20.db", alias="DATABASE_URL")

    # CORS
    frontend_origin: str = Field(default="http://localhost:5173", alias="FRONTEND_ORIGIN")

    # Optional Cloud Provider Keys
    openai_api_key: SecretStr | None = Field(default=None, alias="OPENAI_API_KEY")
    anthropic_api_key: SecretStr | None = Field(default=None, alias="ANTHROPIC_API_KEY")
    gemini_api_key: SecretStr | None = Field(default=None, alias="GEMINI_API_KEY")


@lru_cache
def get_settings() -> Settings:
    """Return cached application settings singleton."""
    return Settings()
