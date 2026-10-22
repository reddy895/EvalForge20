"""Benchmark leaderboard matrix and ranking generator."""

from dataclasses import dataclass
from typing import Sequence

@dataclass
class LeaderboardEntry:
    rank: int
    model_id: str
    model_name: str
    benchmark_name: str
    quality_score: float
    median_latency_ms: float
    tokens_per_second: float | None
    pass_rate_percent: float
    sample_count: int

def generate_leaderboard(runs: Sequence[dict]) -> list[LeaderboardEntry]:
    """Sort and rank runs by quality score descending and latency ascending."""
    entries: list[LeaderboardEntry] = []
    for r in runs:
        score = float(r.get("quality_score", r.get("pass_rate", 0.0)))
        entries.append(
            LeaderboardEntry(
                rank=0,
                model_id=r.get("model_id", "unknown"),
                model_name=r.get("model_name", r.get("model_id", "unknown")),
                benchmark_name=r.get("benchmark_name", "General"),
                quality_score=score,
                median_latency_ms=float(r.get("median_latency_ms", r.get("avg_latency_ms", 0.0))),
                tokens_per_second=r.get("tokens_per_second"),
                pass_rate_percent=float(r.get("pass_rate", score)),
                sample_count=int(r.get("total_cases", 0)),
            )
        )

    # Sort: quality_score DESC, median_latency ASC
    entries.sort(key=lambda e: (-e.quality_score, e.median_latency_ms))
    for idx, entry in enumerate(entries, start=1):
        entry.rank = idx

    return entries
