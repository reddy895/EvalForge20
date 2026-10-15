"""Typed configuration settings for EvalForge20."""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central configuration for EvalForge20."""

    model_config = SettingsConfigDict(
        env_prefix="EVALFORGE20_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Core environment
    env: Literal["development", "testing", "production"] = "development"
    debug: bool = False
    database_url: str = "sqlite:///./data/evalforge20.db"
    log_level: str = "INFO"
    log_prompts: bool = False
    data_dir: Path = Field(default=Path("./data"))

    # Execution controls
    max_concurrency: int = Field(default=5, ge=1, le=50)
    default_timeout_seconds: float = Field(default=60.0, gt=0.0)
    max_output_bytes: int = Field(default=524288, ge=1024)  # 512 KB

    # Local Ollama Provider settings
    ollama_base_url: str = "http://localhost:11434"
    ollama_timeout_seconds: float = Field(default=120.0, gt=0.0)

    # Optional LangSmith settings (supports LANGSMITH_ environment variables directly)
    langsmith_tracing: bool = Field(default=False, validation_alias="LANGSMITH_TRACING")
    langsmith_endpoint: str = Field(
        default="https://api.smith.langchain.com",
        validation_alias="LANGSMITH_ENDPOINT",
    )
    langsmith_api_key: SecretStr | None = Field(
        default=None,
        validation_alias="LANGSMITH_API_KEY",
    )
    langsmith_project: str = Field(
        default="evalforge20-default",
        validation_alias="LANGSMITH_PROJECT",
    )
    langsmith_auto_sync_datasets: bool = Field(
        default=False,
        validation_alias="LANGSMITH_AUTO_SYNC_DATASETS",
    )

    @property
    def is_langsmith_enabled(self) -> bool:
        """Return True only if tracing is enabled and an API key is provided."""
        return (
            bool(self.langsmith_tracing)
            and self.langsmith_api_key is not None
            and bool(self.langsmith_api_key.get_secret_value().strip())
        )

    def ensure_directories(self) -> None:
        """Create necessary data directories if they do not exist."""
        self.data_dir.mkdir(parents=True, exist_ok=True)
        # If database URL points to a local file, ensure its parent directory exists
        if self.database_url.startswith("sqlite:///") and not self.database_url.startswith(
            "sqlite:///:memory:"
        ):
            db_path = Path(self.database_url.replace("sqlite:///", ""))
            db_path.parent.mkdir(parents=True, exist_ok=True)


@lru_cache
def get_settings() -> Settings:
    """Return a cached singleton instance of application settings."""
    settings = Settings()
    settings.ensure_directories()
    return settings
