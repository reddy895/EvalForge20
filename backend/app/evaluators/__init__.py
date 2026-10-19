"""Evaluator contracts and registry for EvalForge20."""

from app.domain.contracts import EvaluatorContract
from app.evaluators.registry import registry

__all__ = [
    "registry",
    "EvaluatorContract",
]
