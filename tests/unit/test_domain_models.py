"""Unit tests for domain models, validation, and lifecycle transitions."""

import pytest
from app.domain.contracts import ProviderRequest, ProviderResponse
from app.domain.errors import (
    NormalizedErrorCategory,
    classify_exception,
)
from app.domain.models import EvaluationCase, TargetConfiguration, TargetType
from app.domain.state import (
    EvaluationRunStatus,
    InvalidStateTransitionError,
    is_terminal_status,
    validate_status_transition,
)
from pydantic import ValidationError


def test_target_configuration_validation():
    """Verify target configuration bounds and defaults."""
    target = TargetConfiguration(
        target_name="test-target",
        target_type=TargetType.MOCK,
        provider_name="mock",
        model_identifier="mock-1",
        temperature=0.7,
    )
    assert target.target_name == "test-target"
    assert target.temperature == 0.7

    # Disallow out-of-range temperatures
    with pytest.raises(ValidationError):
        TargetConfiguration(target_name="bad", temperature=2.5)


def test_evaluation_case_creation():
    """Verify evaluation case model fields and defaults."""
    case = EvaluationCase(
        id="case-101",
        input="Summarize this text",
        expected_output="Summary",
        tags=["nlp", "summarization"],
        category="general",
    )
    assert case.id == "case-101"
    assert case.expected_output == "Summary"
    assert "nlp" in case.tags


def test_evaluation_run_state_transitions():
    """Verify lifecycle state transitions and terminal state detection."""
    # Valid transitions
    validate_status_transition(EvaluationRunStatus.PENDING, EvaluationRunStatus.RUNNING)
    validate_status_transition(EvaluationRunStatus.RUNNING, EvaluationRunStatus.COMPLETED)
    validate_status_transition(
        EvaluationRunStatus.RUNNING, EvaluationRunStatus.COMPLETED_WITH_ERRORS
    )
    validate_status_transition(EvaluationRunStatus.RUNNING, EvaluationRunStatus.FAILED)
    validate_status_transition(EvaluationRunStatus.RUNNING, EvaluationRunStatus.CANCELLED)
    validate_status_transition(EvaluationRunStatus.PENDING, EvaluationRunStatus.CANCELLED)

    # Idempotent same-state transitions
    validate_status_transition(EvaluationRunStatus.RUNNING, EvaluationRunStatus.RUNNING)

    # Invalid transitions
    with pytest.raises(InvalidStateTransitionError):
        validate_status_transition(EvaluationRunStatus.COMPLETED, EvaluationRunStatus.RUNNING)

    with pytest.raises(InvalidStateTransitionError):
        validate_status_transition(EvaluationRunStatus.FAILED, EvaluationRunStatus.COMPLETED)

    with pytest.raises(InvalidStateTransitionError):
        validate_status_transition(EvaluationRunStatus.PENDING, EvaluationRunStatus.COMPLETED)

    # Terminal states
    assert is_terminal_status(EvaluationRunStatus.COMPLETED)
    assert is_terminal_status(EvaluationRunStatus.COMPLETED_WITH_ERRORS)
    assert is_terminal_status(EvaluationRunStatus.FAILED)
    assert is_terminal_status(EvaluationRunStatus.CANCELLED)
    assert not is_terminal_status(EvaluationRunStatus.PENDING)
    assert not is_terminal_status(EvaluationRunStatus.RUNNING)


def test_error_classification():
    """Verify exception classification into normalized categories."""
    cat, _ = classify_exception(TimeoutError("timeout"))
    assert cat == NormalizedErrorCategory.TIMEOUT

    cat, _ = classify_exception(ConnectionRefusedError("Failed to connect: connection refused"))
    assert cat == NormalizedErrorCategory.PROVIDER_UNAVAILABLE

    cat, _ = classify_exception(RuntimeError("HTTP 401 Unauthorized"))
    assert cat == NormalizedErrorCategory.AUTHENTICATION_ERROR

    cat, _ = classify_exception(RuntimeError("Rate limit reached: HTTP 429"))
    assert cat == NormalizedErrorCategory.RATE_LIMIT

    cat, _ = classify_exception(RuntimeError("Prompt is too long: context length exceeded"))
    assert cat == NormalizedErrorCategory.CONTEXT_LENGTH_EXCEEDED


def test_provider_contracts():
    """Verify ProviderRequest and ProviderResponse schemas."""
    req = ProviderRequest(prompt="Hello", temperature=0.5)
    assert req.prompt == "Hello"

    resp = ProviderResponse(
        output_text="Hi there",
        latency_ms=125.4,
        token_usage={"total_tokens": 15},
        is_success=True,
    )
    assert resp.is_success
    assert resp.latency_ms == 125.4
