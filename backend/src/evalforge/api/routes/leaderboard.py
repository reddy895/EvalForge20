"""Modular API route for category-specific model leaderboards based on actual evaluated experiments."""

from typing import Any
from fastapi import APIRouter
from sqlalchemy import select

from src.evalforge.database.models import ExperimentRecord
from src.evalforge.database.session import get_db_context
from src.evalforge.schemas.main import LeaderboardEntry, LeaderboardResponse

router = APIRouter(prefix="/leaderboard", tags=["leaderboard"])

CATEGORY_METRIC_MAP = {
    "Reasoning": "math_correctness",
    "Coding": "functional_correctness",
    "Mathematics": "math_correctness",
    "Knowledge": "normalized_accuracy",
    "Instruction Following": "constraint_satisfaction",
    "Performance": "avg_latency_ms",
    "Efficiency": "tokens_per_second",
    "Reliability": "pass_rate",
    "Safety": "prompt_injection_resistance",
}


@router.get("")
async def get_leaderboard(category: str = "Reasoning") -> dict[str, Any]:
    norm_cat = category.strip().title()
    if norm_cat not in CATEGORY_METRIC_MAP:
        # Fallback to Reasoning if unknown category
        norm_cat = "Reasoning"

    target_metric = CATEGORY_METRIC_MAP[norm_cat]

    async with get_db_context() as session:
        stmt = select(ExperimentRecord).where(ExperimentRecord.status == "COMPLETED")
        res = await session.execute(stmt)
        experiments = res.scalars().all()

        entries: list[LeaderboardEntry] = []
        for exp in experiments:
            metrics = exp.metrics
            score = None
            if target_metric in metrics:
                score = float(metrics[target_metric])
            elif "pass_rate" in metrics and norm_cat in ("Reasoning", "Knowledge", "Coding"):
                score = float(metrics["pass_rate"])

            if score is None:
                continue

            cases_count = metrics.get("total_cases", 0)
            lat = metrics.get("avg_latency_ms")
            hw_dict = exp.hardware
            hw_str = f"{hw_dict.get('os_name', 'Linux')} / {hw_dict.get('cpu_cores', 4)} cores"

            entries.append(LeaderboardEntry(
                rank=0,
                model_identifier=exp.model_identifier,
                category=norm_cat,
                benchmark_dataset=exp.name,
                score=round(score, 4),
                metric_name=target_metric,
                samples_count=cases_count,
                hardware=hw_str,
                latency_ms=float(lat) if lat is not None else None,
                evaluated_at=exp.created_at.strftime("%Y-%m-%d %H:%M"),
                is_verified=True,
            ))

        # Sort entries: ascending for latency, descending for accuracy/scores
        if target_metric == "avg_latency_ms":
            entries.sort(key=lambda x: x.score)
        else:
            entries.sort(key=lambda x: x.score, reverse=True)

        for idx, entry in enumerate(entries, start=1):
            entry.rank = idx

        return {
            "category": norm_cat,
            "total_models": len(entries),
            "entries": [e.model_dump() for e in entries],
            "supported_categories": list(CATEGORY_METRIC_MAP.keys()),
        }
