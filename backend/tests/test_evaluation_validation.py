"""Unit tests for EvaluationCreateRequest and EvaluationConfig validation contracts."""

import pytest
from pydantic import ValidationError

from src.evalforge.schemas.evaluation import EvaluationConfig, EvaluationCreateRequest


class TestEvaluationValidation:
    """Verifies boundary constraints, sanitization, and error handling for evaluation requests."""

    def test_valid_request_constructs_successfully(self) -> None:
        req = EvaluationCreateRequest(
            model_id="qwen2.5:1.5b",
            dataset_id="coding_basics",
            provider="ollama",
            max_cases=5,
            config=EvaluationConfig(temperature=0.7, top_p=0.9, max_tokens=1024),
        )
        assert req.model_id == "qwen2.5:1.5b"
        assert req.dataset_id == "coding_basics"
        assert req.config.temperature == 0.7
        assert req.config.top_p == 0.9

    def test_whitespace_sanitization_trims_identifiers(self) -> None:
        req = EvaluationCreateRequest(
            model_id="  llama3.2:1b  ",
            dataset_id="  structured_json  ",
            provider=" ollama  ",
        )
        assert req.model_id == "llama3.2:1b"
        assert req.dataset_id == "structured_json"
        assert req.provider == "ollama"

    def test_empty_or_whitespace_model_id_rejected(self) -> None:
        with pytest.raises(ValidationError) as exc:
            EvaluationCreateRequest(model_id="   ", dataset_id="ds-1")
        assert "cannot be empty" in str(exc.value)

    def test_empty_dataset_id_rejected(self) -> None:
        with pytest.raises(ValidationError) as exc:
            EvaluationCreateRequest(model_id="llama3.2", dataset_id=" ")
        assert "cannot be empty" in str(exc.value)

    def test_invalid_temperature_boundary_rejected(self) -> None:
        with pytest.raises(ValidationError):
            EvaluationConfig(temperature=2.5)
        with pytest.raises(ValidationError):
            EvaluationConfig(temperature=-0.1)

    def test_invalid_top_p_boundary_rejected(self) -> None:
        with pytest.raises(ValidationError):
            EvaluationConfig(top_p=1.5)
        with pytest.raises(ValidationError):
            EvaluationConfig(top_p=-0.05)

    def test_invalid_max_cases_boundary_rejected(self) -> None:
        with pytest.raises(ValidationError):
            EvaluationCreateRequest(model_id="m1", dataset_id="d1", max_cases=0)
        with pytest.raises(ValidationError):
            EvaluationCreateRequest(model_id="m1", dataset_id="d1", max_cases=50000)
