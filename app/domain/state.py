"""Lifecycle states and transition rules for evaluation runs."""

from enum import Enum


class EvaluationRunStatus(str, Enum):
    """Lifecycle statuses for an evaluation run."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    COMPLETED_WITH_ERRORS = "completed_with_errors"
    FAILED = "failed"
    CANCELLED = "cancelled"


VALID_TRANSITIONS: dict[EvaluationRunStatus, set[EvaluationRunStatus]] = {
    EvaluationRunStatus.PENDING: {
        EvaluationRunStatus.RUNNING,
        EvaluationRunStatus.CANCELLED,
    },
    EvaluationRunStatus.RUNNING: {
        EvaluationRunStatus.COMPLETED,
        EvaluationRunStatus.COMPLETED_WITH_ERRORS,
        EvaluationRunStatus.FAILED,
        EvaluationRunStatus.CANCELLED,
    },
    EvaluationRunStatus.COMPLETED: set(),
    EvaluationRunStatus.COMPLETED_WITH_ERRORS: set(),
    EvaluationRunStatus.FAILED: set(),
    EvaluationRunStatus.CANCELLED: set(),
}


class InvalidStateTransitionError(Exception):
    """Raised when an illegal lifecycle state transition is attempted."""

    def __init__(self, from_state: EvaluationRunStatus, to_state: EvaluationRunStatus):
        super().__init__(
            f"Cannot transition evaluation run from '{from_state.value}' to '{to_state.value}'"
        )
        self.from_state = from_state
        self.to_state = to_state


def is_terminal_status(status: EvaluationRunStatus) -> bool:
    """Check if the evaluation status is terminal."""
    return len(VALID_TRANSITIONS.get(status, set())) == 0


def validate_status_transition(
    current_status: EvaluationRunStatus, next_status: EvaluationRunStatus
) -> None:
    """Validate that transitioning from current_status to next_status is allowed."""
    if next_status == current_status:
        return
    allowed = VALID_TRANSITIONS.get(current_status, set())
    if next_status not in allowed:
        raise InvalidStateTransitionError(current_status, next_status)
