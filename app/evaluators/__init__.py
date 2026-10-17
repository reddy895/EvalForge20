"""Evaluator registry and metric discovery for EvalForge20."""

# Import built-in evaluators to trigger automatic registration
from app.agents import evaluator as agent_evaluators
from app.evaluators import llm_judge
from app.evaluators.code import (
    classification,
    completeness,
    contains_match,
    exact_match,
    json_schema,
    json_validity,
    normalized_match,
    task_assertions,
    token_f1,
)
from app.evaluators.composite import scorer
from app.evaluators.registry import registry
from app.rag import metrics as rag_metrics

__all__ = [
    "agent_evaluators",
    "classification",
    "completeness",
    "contains_match",
    "exact_match",
    "json_schema",
    "json_validity",
    "llm_judge",
    "normalized_match",
    "rag_metrics",
    "registry",
    "scorer",
    "task_assertions",
    "token_f1",
]
