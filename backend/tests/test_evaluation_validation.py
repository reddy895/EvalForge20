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

    def test_missing_model_id_field_rejected(self) -> None:
        with pytest.raises(ValidationError) as exc:
            EvaluationCreateRequest(dataset_id="d1")  # type: ignore
        assert "Field required" in str(exc.value) or "model_id" in str(exc.value)

    @pytest.mark.asyncio
    async def test_evaluation_service_validates_model_identifier(self) -> None:
        from unittest.mock import AsyncMock, MagicMock
        from src.evalforge.core.errors import DataValidationError
        from src.evalforge.services.evaluation_service import EvaluationService

        mock_eval_repo = MagicMock()
        mock_ds_repo = MagicMock()
        mock_dataset = MagicMock()
        mock_dataset.test_cases = [MagicMock()]
        mock_dataset.name = "Test DS"
        mock_ds_repo.get_with_cases = AsyncMock(return_value=mock_dataset)

        service = EvaluationService(eval_repo=mock_eval_repo, dataset_repo=mock_ds_repo)

        req = EvaluationCreateRequest(model_id="qwen2.5:1.5b", dataset_id="ds-1")
        req.model_id = ""  # Bypass pydantic to test service defense-in-depth

        with pytest.raises(DataValidationError, match="Target model identifier must be specified"):
            await service.create_and_start_run(req)

    @pytest.mark.asyncio
    async def test_duplicate_evaluation_request_throttling(self) -> None:
        """When an identical evaluation is requested within the debounce window, existing run is returned."""
        from unittest.mock import AsyncMock, MagicMock
        from src.evalforge.services.evaluation_service import EvaluationService
        from src.evalforge.storage.models.evaluation import EvaluationRun

        mock_eval_repo = MagicMock()
        mock_ds_repo = MagicMock()
        mock_dataset = MagicMock()
        mock_dataset.id = "ds-1"
        mock_dataset.test_cases = [MagicMock()]
        mock_dataset.name = "Test DS"
        mock_ds_repo.get_with_cases = AsyncMock(return_value=mock_dataset)

        existing_run = EvaluationRun(
            id="existing-run-id-123",
            name="Existing Run",
            model_id="qwen2.5:1.5b",
            provider="ollama",
            dataset_id="ds-1",
            status="running",
        )
        mock_eval_repo.find_recent_duplicate = AsyncMock(return_value=existing_run)
        mock_eval_repo.add = AsyncMock()

        service = EvaluationService(eval_repo=mock_eval_repo, dataset_repo=mock_ds_repo)

        req = EvaluationCreateRequest(model_id="qwen2.5:1.5b", dataset_id="ds-1")
        returned_run = await service.create_and_start_run(req)

        assert returned_run.id == "existing-run-id-123"
        mock_eval_repo.add.assert_not_called()  # Reused existing run, didn't create duplicate!

    @pytest.mark.asyncio
    async def test_uninstalled_ollama_model_rejected_with_remediation(self) -> None:
        """Reject uninstalled Ollama models with a descriptive remediation hint."""
        from unittest.mock import AsyncMock, MagicMock
        from src.evalforge.core.errors import DataValidationError
        from src.evalforge.services.evaluation_service import EvaluationService

        mock_eval_repo = MagicMock()
        mock_ds_repo = MagicMock()
        mock_dataset = MagicMock()
        mock_dataset.test_cases = [MagicMock()]
        mock_dataset.name = "Test DS"
        mock_ds_repo.get_with_cases = AsyncMock(return_value=mock_dataset)

        mock_provider = MagicMock()
        mock_provider.check_model_readiness = AsyncMock(
            return_value={
                "ready": False,
                "remediation_hint": "Model 'nonexistent:latest' is not installed locally. Run `ollama pull nonexistent:latest` to install.",
            }
        )
        mock_registry = MagicMock()
        mock_registry.get.return_value = mock_provider

        service = EvaluationService(
            eval_repo=mock_eval_repo,
            dataset_repo=mock_ds_repo,
            registry=mock_registry,
        )

        req = EvaluationCreateRequest(
            model_id="nonexistent:latest",
            dataset_id="ds-1",
            provider="ollama",
        )
        with pytest.raises(DataValidationError, match="ollama pull nonexistent:latest"):
            await service.create_and_start_run(req)

