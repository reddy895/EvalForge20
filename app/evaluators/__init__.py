"""Evaluator registry and metric discovery for EvalForge20."""

# Import built-in evaluators to trigger automatic registration
from app.evaluators.code import (
    exact_match,
    json_schema,
    json_validity,
    normalized_match,
    task_assertions,
)
from app.evaluators.registry import registry

__all__ = [
    "exact_match",
    "json_schema",
    "json_validity",
    "normalized_match",
    "registry",
    "task_assertions",
]
