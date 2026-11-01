"""Strict visual workflow graph parser and topological validator."""

from collections import defaultdict, deque
from typing import Any

from src.evalforge.schemas.main import (
    WorkflowGraph,
    WorkflowValidationError,
    WorkflowValidationResult,
)


class WorkflowValidator:
    """Validates connectivity, component presence, and execution paths in React Flow graphs."""

    VALID_NODE_TYPES = {"model", "dataset", "evaluator", "benchmark"}

    @classmethod
    def validate_graph(cls, graph: WorkflowGraph) -> WorkflowValidationResult:
        errors: list[WorkflowValidationError] = []
        warnings: list[WorkflowValidationError] = []

        nodes_by_id = {n.id: n for n in graph.nodes}
        nodes_by_type: dict[str, list[Any]] = defaultdict(list)
        for n in graph.nodes:
            nodes_by_type[n.type].append(n)

        # 1. Structural requirements
        models = nodes_by_type.get("model", [])
        datasets = nodes_by_type.get("dataset", []) + nodes_by_type.get("benchmark", [])
        evaluators = nodes_by_type.get("evaluator", [])

        if not models:
            errors.append(WorkflowValidationError(
                message="Workflow requires at least one Model node to evaluate.",
                severity="error",
            ))

        if not datasets:
            errors.append(WorkflowValidationError(
                message="Workflow requires at least one Dataset or Benchmark node.",
                severity="error",
            ))

        if not evaluators:
            errors.append(WorkflowValidationError(
                message="Workflow requires at least one Evaluator node (e.g. Accuracy, Latency).",
                severity="error",
            ))

        # 2. Connection Adjacency
        outgoing = defaultdict(list)
        incoming = defaultdict(list)

        for edge in graph.edges:
            src = nodes_by_id.get(edge.source)
            tgt = nodes_by_id.get(edge.target)

            if not src:
                errors.append(WorkflowValidationError(
                    edge_id=edge.id,
                    message=f"Edge references non-existent source node '{edge.source}'.",
                    severity="error",
                ))
                continue
            if not tgt:
                errors.append(WorkflowValidationError(
                    edge_id=edge.id,
                    message=f"Edge references non-existent target node '{edge.target}'.",
                    severity="error",
                ))
                continue

            # Validate valid connection pairs
            # Valid: dataset -> model, dataset -> evaluator, model -> evaluator
            if src.type in ("dataset", "benchmark") and tgt.type not in ("model", "evaluator"):
                errors.append(WorkflowValidationError(
                    edge_id=edge.id,
                    message=f"Dataset '{src.name}' can only connect to a Model or Evaluator, not '{tgt.type}'.",
                    severity="error",
                ))
            elif src.type == "model" and tgt.type != "evaluator":
                errors.append(WorkflowValidationError(
                    edge_id=edge.id,
                    message=f"Model '{src.name}' can only connect to an Evaluator, not '{tgt.type}'.",
                    severity="error",
                ))
            elif src.type == "evaluator":
                warnings.append(WorkflowValidationError(
                    edge_id=edge.id,
                    message=f"Evaluator '{src.name}' typically has no outgoing connections.",
                    severity="warning",
                ))

            outgoing[edge.source].append(edge.target)
            incoming[edge.target].append(edge.source)

        # 3. Model Connectivity Checks
        executable_models: list[str] = []
        for m in models:
            model_id = m.data.get("model_identifier") or m.name
            has_dataset_input = any(
                nodes_by_id[src_id].type in ("dataset", "benchmark")
                for src_id in incoming.get(m.id, [])
                if src_id in nodes_by_id
            )
            has_evaluator_output = any(
                nodes_by_id[tgt_id].type == "evaluator"
                for tgt_id in outgoing.get(m.id, [])
                if tgt_id in nodes_by_id
            )

            if not has_dataset_input:
                errors.append(WorkflowValidationError(
                    node_id=m.id,
                    message=f"Model '{m.name}' has no incoming Dataset connection.",
                    severity="error",
                ))
            if not has_evaluator_output:
                warnings.append(WorkflowValidationError(
                    node_id=m.id,
                    message=f"Model '{m.name}' is not connected to any Evaluator nodes.",
                    severity="warning",
                ))

            if has_dataset_input and has_evaluator_output:
                executable_models.append(model_id)

        # 4. Cycle Detection
        in_degree = {nid: len(incoming[nid]) for nid in nodes_by_id}
        queue = deque([nid for nid, deg in in_degree.items() if deg == 0])
        visited_count = 0
        while queue:
            curr = queue.popleft()
            visited_count += 1
            for neighbor in outgoing[curr]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        if visited_count < len(nodes_by_id):
            errors.append(WorkflowValidationError(
                message="Workflow graph contains an invalid circular connection / dependency cycle.",
                severity="error",
            ))

        executable_evaluators = [
            e.data.get("evaluator_id") or e.name
            for e in evaluators
            if any(nodes_by_id[s].type == "model" for s in incoming.get(e.id, []) if s in nodes_by_id)
        ]

        dataset_cases_count = 0
        for d in datasets:
            cases = d.data.get("cases", [])
            dataset_cases_count += len(cases)

        is_valid = len(errors) == 0

        return WorkflowValidationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            executable_models=executable_models,
            executable_evaluators=executable_evaluators,
            dataset_records_count=dataset_cases_count,
        )


__all__ = ["WorkflowValidator"]
