"""Modular API route for evaluator metadata and available metric plugins."""

from typing import Any
from fastapi import APIRouter

from src.evalforge.engine.registry import EngineRegistry

router = APIRouter(prefix="/evaluators", tags=["evaluators"])

AVAILABLE_EVALUATOR_METADATA = [
    {
        "evaluator_id": "exact_match",
        "name": "Exact Match",
        "category": "Accuracy & Quality",
        "description": "Strict string equality check between candidate prediction and reference target.",
        "is_deterministic": True,
        "required_inputs": ["prediction", "reference"],
    },
    {
        "evaluator_id": "normalized_accuracy",
        "name": "Normalized Accuracy",
        "category": "Accuracy & Quality",
        "description": "Normalized text equality ignoring casing, whitespace, and punctuation.",
        "is_deterministic": True,
        "required_inputs": ["prediction", "reference"],
    },
    {
        "evaluator_id": "token_f1",
        "name": "Token F1 Score",
        "category": "Accuracy & Quality",
        "description": "Token-level precision, recall, and harmonic F1 score.",
        "is_deterministic": True,
        "required_inputs": ["prediction", "reference"],
    },
    {
        "evaluator_id": "classification_accuracy",
        "name": "Classification Accuracy",
        "category": "Accuracy & Quality",
        "description": "Categorical label classification accuracy.",
        "is_deterministic": True,
        "required_inputs": ["prediction", "reference"],
    },
    {
        "evaluator_id": "math_correctness",
        "name": "Mathematical Correctness",
        "category": "Reasoning",
        "description": "Numeric extraction, fractions, and tolerance comparison.",
        "is_deterministic": True,
        "required_inputs": ["prediction", "reference"],
    },
    {
        "evaluator_id": "constraint_satisfaction",
        "name": "Constraint Satisfaction",
        "category": "Reasoning",
        "description": "Verifies word count bounds, prefix rules, and forbidden phrases.",
        "is_deterministic": True,
        "required_inputs": ["prediction"],
    },
    {
        "evaluator_id": "functional_correctness",
        "name": "Functional Correctness",
        "category": "Coding",
        "description": "Sandboxed Python execution with AST verification and unit tests.",
        "is_deterministic": True,
        "required_inputs": ["prediction"],
    },
    {
        "evaluator_id": "latency",
        "name": "Latency SLA",
        "category": "Performance",
        "description": "Measures response time in ms against configured SLA threshold.",
        "is_deterministic": True,
        "required_inputs": ["prediction"],
    },
    {
        "evaluator_id": "tokens_per_second",
        "name": "Tokens Per Second",
        "category": "Performance",
        "description": "Measures output generation throughput speed.",
        "is_deterministic": True,
        "required_inputs": ["prediction"],
    },
    {
        "evaluator_id": "reliability",
        "name": "Reliability & Success Rate",
        "category": "Reliability",
        "description": "Tracks timeout rate, error rate, and response integrity.",
        "is_deterministic": True,
        "required_inputs": ["prediction"],
    },
    {
        "evaluator_id": "prompt_injection_resistance",
        "name": "Prompt Injection Resistance",
        "category": "Safety",
        "description": "Evaluates resistance against adversarial jailbreaks and overrides.",
        "is_deterministic": True,
        "required_inputs": ["prediction"],
    },
    {
        "evaluator_id": "sensitive_leakage",
        "name": "Sensitive Leakage Prevention",
        "category": "Safety",
        "description": "Detects accidental disclosure of API keys, PII, and credentials.",
        "is_deterministic": True,
        "required_inputs": ["prediction"],
    },
    {
        "evaluator_id": "refusal_quality",
        "name": "Refusal Quality",
        "category": "Safety",
        "description": "Verifies professional refusal when encountering harmful prompts.",
        "is_deterministic": True,
        "required_inputs": ["prediction"],
    },
    {
        "evaluator_id": "json_validity",
        "name": "JSON Validity",
        "category": "Structured Output",
        "description": "Verifies that output conforms to RFC 8259 JSON syntax.",
        "is_deterministic": True,
        "required_inputs": ["prediction"],
    },
    {
        "evaluator_id": "json_schema_compliance",
        "name": "JSON Schema Compliance",
        "category": "Structured Output",
        "description": "Validates JSON structure and required fields against schema.",
        "is_deterministic": True,
        "required_inputs": ["prediction"],
    },
    {
        "evaluator_id": "rag_faithfulness",
        "name": "RAG Faithfulness",
        "category": "RAG",
        "description": "Measures grounding of generated statements against retrieved context.",
        "is_deterministic": True,
        "required_inputs": ["prediction", "context"],
    },
    {
        "evaluator_id": "rag_context_relevance",
        "name": "RAG Context Relevance",
        "category": "RAG",
        "description": "Measures overlap between user query and retrieved context.",
        "is_deterministic": True,
        "required_inputs": ["prediction", "reference"],
    },
    {
        "evaluator_id": "judge",
        "name": "Local LLM Judge",
        "category": "Model-Judged",
        "description": "Qualitative rubric-based evaluation using an independent local Ollama model.",
        "is_deterministic": False,
        "required_inputs": ["prediction"],
    },
]


@router.get("")
async def list_evaluators() -> dict[str, Any]:
    return {
        "total": len(AVAILABLE_EVALUATOR_METADATA),
        "evaluators": AVAILABLE_EVALUATOR_METADATA,
    }
