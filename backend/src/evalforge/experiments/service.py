"""Experiment service orchestrating comparisons, deltas, and lifecycle management."""

import json
from typing import Any

from src.evalforge.database.models import ExperimentRecord
from src.evalforge.experiments.repository import ExperimentRepository


class ExperimentService:
    """Business logic service for managing experiments, multi-model comparisons, and deltas."""

    @classmethod
    async def get_experiment(cls, experiment_id: str) -> dict[str, Any] | None:
        return await ExperimentRepository.export_json(experiment_id)

    @classmethod
    async def list_experiments(
        cls, limit: int = 50, offset: int = 0, model_identifier: str | None = None
    ) -> list[dict[str, Any]]:
        records = await ExperimentRepository.list_all(
            limit=limit, offset=offset, model_identifier=model_identifier
        )
        results = []
        for r in records:
            results.append({
                "id": r.id,
                "name": r.name,
                "model_identifier": r.model_identifier,
                "workflow_id": r.workflow_id,
                "dataset_id": r.dataset_id,
                "evaluator_ids": json.loads(r.evaluator_ids_json),
                "metrics": json.loads(r.metrics_json),
                "parameters": json.loads(r.parameters_json),
                "hardware": json.loads(r.hardware_json),
                "status": r.status,
                "created_at": r.created_at.isoformat(),
            })
        return results

    @classmethod
    async def delete_experiment(cls, experiment_id: str) -> bool:
        return await ExperimentRepository.delete(experiment_id)

    @classmethod
    async def compare_experiments(cls, experiment_ids: list[str]) -> dict[str, Any]:
        """Aggregate side-by-side metrics and relative differences across multiple experiments."""
        experiments: list[dict[str, Any]] = []
        for eid in experiment_ids:
            exp = await ExperimentRepository.export_json(eid)
            if exp:
                experiments.append(exp)

        if not experiments:
            return {
                "experiments": [],
                "metric_comparison": {},
                "latency_comparison": {},
                "reliability_comparison": {},
                "efficiency_comparison": {},
            }

        # Build comparison matrices
        metric_comparison: dict[str, dict[str, float]] = {}
        latency_comparison: dict[str, float] = {}
        reliability_comparison: dict[str, float] = {}
        efficiency_comparison: dict[str, dict[str, float]] = {}

        for exp in experiments:
            model_key = exp["model_identifier"]
            metrics = exp.get("metrics", {})

            # 1. Standard metrics
            for m_key, m_val in metrics.items():
                if isinstance(m_val, (int, float)):
                    metric_comparison.setdefault(m_key, {})[model_key] = float(m_val)
                elif isinstance(m_val, dict) and "score" in m_val:
                    metric_comparison.setdefault(m_key, {})[model_key] = float(m_val["score"])

            # 2. Latency comparison
            lat = metrics.get("avg_latency_ms") or metrics.get("latency_ms") or metrics.get("latency", {}).get("average_latency_ms")
            if lat is not None:
                latency_comparison[model_key] = float(lat)

            # 3. Reliability comparison
            rel = metrics.get("pass_rate") or metrics.get("success_rate") or metrics.get("reliability", {}).get("success_rate")
            if rel is not None:
                reliability_comparison[model_key] = float(rel)

            # 4. Efficiency comparison
            tps = metrics.get("avg_tokens_per_second") or metrics.get("tokens_per_second", {}).get("tokens_per_second")
            if tps is not None:
                efficiency_comparison.setdefault("tokens_per_sec", {})[model_key] = float(tps)

        return {
            "experiments": experiments,
            "metric_comparison": metric_comparison,
            "latency_comparison": latency_comparison,
            "reliability_comparison": reliability_comparison,
            "efficiency_comparison": efficiency_comparison,
        }


__all__ = ["ExperimentService"]
