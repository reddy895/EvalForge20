"""Workflow execution registry resolving graph nodes to runtime evaluators, datasets, and models."""

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any

from src.evalforge.datasets.loader import ParsedDatasetRecord
from src.evalforge.datasets.registry import get_benchmark_registry
from src.evalforge.evaluators.accuracy import ExactMatchEvaluator, NormalizedAccuracyEvaluator
from src.evalforge.evaluators.agent import AgentTaskCompletionEvaluator, AgentToolCallEvaluator
from src.evalforge.evaluators.base import BaseEvaluator
from src.evalforge.evaluators.classification import ClassificationAccuracyEvaluator, TokenF1Evaluator
from src.evalforge.evaluators.coding import FunctionalCorrectnessEvaluator
from src.evalforge.evaluators.judge import LocalJudgeEvaluator
from src.evalforge.evaluators.performance import LatencyEvaluator, TokensPerSecondEvaluator
from src.evalforge.evaluators.rag import (
    AnswerRelevanceEvaluator,
    ContextPrecisionEvaluator,
    ContextRelevanceEvaluator,
    FaithfulnessEvaluator,
)
from src.evalforge.evaluators.reasoning import ConstraintSatisfactionEvaluator, MathCorrectnessEvaluator
from src.evalforge.evaluators.reliability import ReliabilityEvaluator
from src.evalforge.evaluators.safety import (
    PromptInjectionResistanceEvaluator,
    RefusalQualityEvaluator,
    SensitiveLeakageEvaluator,
)
from src.evalforge.evaluators.structured_output import JsonSchemaEvaluator, JsonValidityEvaluator
from src.evalforge.providers.base import BaseProvider
from src.evalforge.providers.registry import get_provider_registry
from src.evalforge.schemas.main import WorkflowGraph


@dataclass
class ModelExecutionTarget:
    model_node_id: str
    model_identifier: str
    provider_name: str
    dataset_records: list[ParsedDatasetRecord] = field(default_factory=list)
    evaluators: list[BaseEvaluator] = field(default_factory=list)


class EngineRegistry:
    """Instantiates and coordinates evaluators, datasets, and model execution targets from a workflow graph."""

    def __init__(self) -> None:
        self.provider_registry = get_provider_registry()
        self.benchmark_registry = get_benchmark_registry()

    def resolve_evaluator(self, evaluator_id_or_name: str, judge_provider: BaseProvider | None = None) -> BaseEvaluator:
        eid = evaluator_id_or_name.lower().strip()
        if eid in ("exact_match", "exactmatch"):
            return ExactMatchEvaluator()
        elif eid in ("normalized_accuracy", "accuracy", "normalizedaccuracy"):
            return NormalizedAccuracyEvaluator()
        elif eid in ("token_f1", "f1", "f1_score"):
            return TokenF1Evaluator()
        elif eid in ("classification_accuracy", "classification"):
            return ClassificationAccuracyEvaluator()
        elif eid in ("math_correctness", "mathematics", "math"):
            return MathCorrectnessEvaluator()
        elif eid in ("constraint_satisfaction", "reasoning", "constraints"):
            return ConstraintSatisfactionEvaluator()
        elif eid in ("functional_correctness", "coding", "code_execution"):
            return FunctionalCorrectnessEvaluator()
        elif eid in ("latency", "latency_sla", "performance"):
            return LatencyEvaluator()
        elif eid in ("tokens_per_second", "tps", "throughput"):
            return TokensPerSecondEvaluator()
        elif eid in ("reliability", "success_rate"):
            return ReliabilityEvaluator()
        elif eid in ("prompt_injection_resistance", "prompt_injection"):
            return PromptInjectionResistanceEvaluator()
        elif eid in ("sensitive_leakage", "leakage"):
            return SensitiveLeakageEvaluator()
        elif eid in ("refusal_quality", "safety"):
            return RefusalQualityEvaluator()
        elif eid in ("json_validity", "json"):
            return JsonValidityEvaluator()
        elif eid in ("json_schema_compliance", "json_schema"):
            return JsonSchemaEvaluator()
        elif eid in ("rag_faithfulness", "faithfulness"):
            return FaithfulnessEvaluator()
        elif eid in ("rag_context_relevance", "context_relevance"):
            return ContextRelevanceEvaluator()
        elif eid in ("rag_answer_relevance", "answer_relevance"):
            return AnswerRelevanceEvaluator()
        elif eid in ("rag_context_precision", "context_precision"):
            return ContextPrecisionEvaluator()
        elif eid in ("agent_tool_calling", "tool_calling"):
            return AgentToolCallEvaluator()
        elif eid in ("agent_task_completion", "agent_completion"):
            return AgentTaskCompletionEvaluator()
        elif eid in ("judge", "llm_judge", "local_judge"):
            provider = judge_provider or self.provider_registry.get("ollama")
            return LocalJudgeEvaluator(provider=provider, judge_model="qwen2.5:3b")

        # Fallback to normalized accuracy
        return NormalizedAccuracyEvaluator()

    def build_execution_targets(
        self, graph: WorkflowGraph, judge_model: str | None = None
    ) -> list[ModelExecutionTarget]:
        nodes_by_id = {n.id: n for n in graph.nodes}
        outgoing = defaultdict(list)
        incoming = defaultdict(list)

        for edge in graph.edges:
            outgoing[edge.source].append(edge.target)
            incoming[edge.target].append(edge.source)

        model_nodes = [n for n in graph.nodes if n.type == "model"]
        targets: list[ModelExecutionTarget] = []

        judge_provider = self.provider_registry.get("ollama")

        for m_node in model_nodes:
            model_id = m_node.data.get("model_identifier") or m_node.name
            provider_name = m_node.data.get("provider", "ollama")

            # Collect connected datasets / benchmarks
            records: list[ParsedDatasetRecord] = []
            for src_id in incoming.get(m_node.id, []):
                src = nodes_by_id.get(src_id)
                if not src:
                    continue
                if src.type == "dataset":
                    cases = src.data.get("cases", [])
                    for c in cases:
                        records.append(ParsedDatasetRecord(
                            input=c.get("input") or c.get("prompt", ""),
                            expected_output=c.get("expected_output") or c.get("reference"),
                            context=c.get("context"),
                            metadata=c.get("metadata", {}),
                        ))
                elif src.type == "benchmark":
                    suite_id = src.data.get("suite_id") or src.data.get("id")
                    suite = self.benchmark_registry.get_suite(suite_id) if suite_id else None
                    if suite:
                        for c in suite.cases:
                            records.append(ParsedDatasetRecord(
                                input=c["input"],
                                expected_output=c.get("expected_output"),
                                context=c.get("context"),
                                metadata=c.get("metadata", {}),
                            ))

            # Collect connected evaluators
            evaluators: list[BaseEvaluator] = []
            for tgt_id in outgoing.get(m_node.id, []):
                tgt = nodes_by_id.get(tgt_id)
                if tgt and tgt.type == "evaluator":
                    ev_id = tgt.data.get("evaluator_id") or tgt.name
                    ev_instance = self.resolve_evaluator(ev_id, judge_provider=judge_provider)
                    evaluators.append(ev_instance)

            targets.append(ModelExecutionTarget(
                model_node_id=m_node.id,
                model_identifier=model_id,
                provider_name=provider_name,
                dataset_records=records,
                evaluators=evaluators,
            ))

        return targets


__all__ = [
    "EngineRegistry",
    "ModelExecutionTarget",
]
