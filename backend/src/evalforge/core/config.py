"""Application configuration using Pydantic Settings."""

from functools import lru_cache

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    APP_NAME: str = "EvalForge20"
    APP_VERSION: str = "2.1.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"

    # Storage paths
    STORAGE_DIR: str = "./data"

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

    # HTTP request guardrails
    MAX_REQUEST_BODY_BYTES: int = 20 * 1024 * 1024  # 20MB hard ceiling
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_REQUESTS_PER_MINUTE: int = 240
    # Only trust X-Forwarded-For when a trusted reverse proxy overwrites it.
    TRUST_PROXY_HEADERS: bool = False

    # Optional shared-secret authentication for single-user / self-hosted deployments.
    # When AUTH_TOKEN is set, every /api route except health probes requires
    # "Authorization: Bearer <token>". Leave empty for local-only usage.
    AUTH_TOKEN: str | None = None

    # Provider endpoint address policy. Local-first installs need private
    # addresses (localhost / LAN Ollama); public deployments that only use
    # cloud APIs should disable this to reduce SSRF exposure.
    ALLOW_PRIVATE_PROVIDER_ENDPOINTS: bool = True

    # Comma-separated hostnames permitted for provider endpoints (empty = allow all public hosts).
    ALLOWED_PROVIDER_HOSTS: list[str] | str = []

    # CORS
    CORS_ORIGINS: list[str] | str = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
    ]

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"  # "json" or "console"

    @field_validator("ALLOWED_PROVIDER_HOSTS", mode="before")
    @classmethod
    def assemble_allowed_hosts(cls, v: object) -> list[str]:
        if v is None or v == "":
            return []
        if isinstance(v, str):
            return [item.strip().lower() for item in v.split(",") if item.strip()]
        if isinstance(v, list):
            return [str(item).strip().lower() for item in v if str(item).strip()]
        raise ValueError(f"Unexpected type for ALLOWED_PROVIDER_HOSTS: {type(v)}")

    @model_validator(mode="after")
    def validate_security_posture(self) -> "Settings":
        if self.ENVIRONMENT.lower() == "production":
            if self.DEBUG:
                raise ValueError("DEBUG must be disabled in production.")
            if any(origin.strip() == "*" for origin in self.CORS_ORIGINS):
                raise ValueError("Wildcard CORS origins are not allowed in production.")
            if self.HOST not in ("127.0.0.1", "localhost", "::1") and not self.AUTH_TOKEN:
                raise ValueError(
                    "AUTH_TOKEN is required in production when binding to a non-loopback host. "
                    "Set AUTH_TOKEN or keep HOST=127.0.0.1 behind a trusted reverse proxy."
                )
        if self.MAX_REQUEST_BODY_BYTES < 1024:
            raise ValueError("MAX_REQUEST_BODY_BYTES must be at least 1024 bytes.")
        if self.RATE_LIMIT_REQUESTS_PER_MINUTE < 1:
            raise ValueError("RATE_LIMIT_REQUESTS_PER_MINUTE must be positive.")
        return self

    @field_validator("DEBUG", mode="before")
    @classmethod
    def assemble_debug(cls, v: object) -> bool:
        if isinstance(v, bool):
            return v
        if isinstance(v, (int, float)):
            return bool(v)
        if isinstance(v, str):
            return v.strip().lower() in ("true", "1", "t", "yes", "y", "debug")
        return False

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
