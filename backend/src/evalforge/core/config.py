"""Application configuration using Pydantic Settings."""

from functools import lru_cache

from pydantic import field_validator
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

    # Provider Timeout & Resilience
    PROVIDER_TIMEOUT_SECONDS: float = 60.0
    PROVIDER_MAX_RETRIES: int = 2

    # Cloud Provider Settings (Optional, local-first by default)
    OPENAI_API_KEY: str | None = None
    OPENAI_BASE_URL: str = "https://api.openai.com/v1"

    ANTHROPIC_API_KEY: str | None = None
    ANTHROPIC_BASE_URL: str = "https://api.anthropic.com/v1"

    GEMINI_API_KEY: str | None = None
    GEMINI_BASE_URL: str = "https://generativelanguage.googleapis.com/v1beta"

    GROQ_API_KEY: str | None = None
    GROQ_BASE_URL: str = "https://api.groq.com/openai/v1"

    MISTRAL_API_KEY: str | None = None
    MISTRAL_BASE_URL: str = "https://api.mistral.ai/v1"

    COHERE_API_KEY: str | None = None
    COHERE_BASE_URL: str = "https://api.cohere.com/v2"

    TOGETHER_API_KEY: str | None = None
    TOGETHER_BASE_URL: str = "https://api.together.xyz/v1"

    FIREWORKS_API_KEY: str | None = None
    FIREWORKS_BASE_URL: str = "https://api.fireworks.ai/inference/v1"

    DEEPSEEK_API_KEY: str | None = None
    DEEPSEEK_BASE_URL: str = "https://api.deepseek.com/v1"

    HUGGINGFACE_API_KEY: str | None = None
    HUGGINGFACE_BASE_URL: str = "https://api-inference.huggingface.co/models"

    AZURE_OPENAI_API_KEY: str | None = None
    AZURE_OPENAI_ENDPOINT: str | None = None
    AZURE_OPENAI_API_VERSION: str = "2024-02-15-preview"

    AWS_ACCESS_KEY_ID: str | None = None
    AWS_SECRET_ACCESS_KEY: str | None = None
    AWS_REGION: str = "us-east-1"

    GENERIC_OPENAI_API_KEY: str | None = None
    GENERIC_OPENAI_BASE_URL: str = "http://localhost:8080/v1"

    # Concurrency and Limits
    DEFAULT_CONCURRENCY_LIMIT: int = 4
    MAX_CONCURRENCY_LIMIT: int = 16
    MAX_DATASET_FILE_SIZE_BYTES: int = 10 * 1024 * 1024  # 10MB
    MAX_CASES_PER_DATASET: int = 2000

    # CORS
    CORS_ORIGINS: list[str] | str = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
    ]

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"  # "json" or "console"

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: object) -> list[str]:
        default_origins = [
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://localhost:3000",
        ]
        if v is None:
            return default_origins
        if isinstance(v, str):
            v_str = v.strip()
            if not v_str:
                return default_origins
            if v_str.startswith("[") or v_str.endswith("]"):
                import json
                try:
                    parsed = json.loads(v_str)
                except Exception as exc:
                    raise ValueError(f"Malformed JSON string in CORS_ORIGINS: {exc}") from exc
                if not isinstance(parsed, list):
                    raise ValueError("CORS_ORIGINS JSON must be a list of origin URLs")
                return [str(item).strip() for item in parsed if str(item).strip()]
            origins = [x.strip() for x in v_str.split(",") if x.strip()]
            return origins if origins else default_origins
        if isinstance(v, list):
            return [str(x).strip() for x in v if str(x).strip()]
        raise ValueError(f"Unexpected type for CORS_ORIGINS: {type(v)}")


@lru_cache
def get_settings() -> Settings:
    """Return cached application settings instance."""
    return Settings()
