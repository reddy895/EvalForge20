"""Unit tests verifying CORS_ORIGINS parsing in Settings."""

import os
import pytest
from pydantic import ValidationError
from src.evalforge.core.config import Settings


def test_cors_origins_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("CORS_ORIGINS", raising=False)
    settings = Settings()
    assert "http://localhost:5173" in settings.CORS_ORIGINS
    assert "http://127.0.0.1:5173" in settings.CORS_ORIGINS
    assert "http://localhost:3000" in settings.CORS_ORIGINS


def test_cors_origins_comma_separated(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:8000,http://127.0.0.1:5173")
    settings = Settings()
    assert settings.CORS_ORIGINS == [
        "http://localhost:5173",
        "http://localhost:8000",
        "http://127.0.0.1:5173",
    ]


def test_cors_origins_json_array(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CORS_ORIGINS", '["http://app.local", "http://test.local"]')
    settings = Settings()
    assert settings.CORS_ORIGINS == ["http://app.local", "http://test.local"]


def test_cors_origins_empty_string_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CORS_ORIGINS", "   ")
    settings = Settings()
    assert len(settings.CORS_ORIGINS) >= 2
    assert "http://localhost:5173" in settings.CORS_ORIGINS


def test_cors_origins_malformed_json_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CORS_ORIGINS", "[invalid json string")
    with pytest.raises(ValidationError):
        Settings()
