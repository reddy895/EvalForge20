"""Benchmark leaderboard matrix and ranking generator."""

from collections.abc import Sequence
from dataclasses import dataclass


@dataclass
class LeaderboardEntry:
    rank: int
    model_id: str
    model_name: str
    benchmark_name: str
    quality_score: float
    median_latency_ms: float | None
    p95_latency_ms: float | None = None
    tokens_per_second: float | None = None
    pass_rate_percent: float = 0.0
    sample_count: int = 0
    provider: str = "ollama"
    run_status: str = "completed"
    timestamp: str | None = None

def generate_leaderboard(runs: Sequence[dict]) -> list[LeaderboardEntry]:
    """Sort and rank runs by quality score descending and latency ascending."""
    entries: list[LeaderboardEntry] = []
    for r in runs:
        score = float(r.get("quality_score", r.get("pass_rate", 0.0)))
        raw_lat = r.get("median_latency_ms") if r.get("median_latency_ms") is not None else r.get("avg_latency_ms")
        med_lat = float(raw_lat) if raw_lat is not None and float(raw_lat) > 0 else None
        p95_lat = float(r["p95_latency_ms"]) if r.get("p95_latency_ms") is not None and float(r["p95_latency_ms"]) > 0 else None
        tps = float(r["tokens_per_second"]) if r.get("tokens_per_second") is not None else None

        entries.append(
            LeaderboardEntry(
                rank=0,
                model_id=r.get("model_id", "unknown"),
                model_name=r.get("model_name", r.get("model_id", "unknown")),
                benchmark_name=r.get("benchmark_name", "General"),
                quality_score=score,
                median_latency_ms=med_lat,
                p95_latency_ms=p95_lat,
                tokens_per_second=tps,
                pass_rate_percent=float(r.get("pass_rate", score)),
                sample_count=int(r.get("total_cases", 0)),
                provider=r.get("provider", "ollama"),
                run_status=r.get("run_status", "completed"),
                timestamp=r.get("timestamp"),
            )
        )

    # Sort: quality_score DESC, median_latency ASC (None latency ranked after valid latencies)
    def sort_key(e: LeaderboardEntry) -> tuple[float, float]:
        lat = e.median_latency_ms if e.median_latency_ms is not None else float("inf")
        return (-e.quality_score, lat)

    entries.sort(key=sort_key)
    for idx, entry in enumerate(entries, start=1):
        entry.rank = idx

    return entries
