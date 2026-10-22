"""Unit tests for benchmark leaderboard ranking."""

from src.evalforge.analytics.leaderboard import generate_leaderboard


def test_generate_leaderboard_ranking() -> None:
    runs = [
        {"model_id": "model_b", "quality_score": 85.0, "median_latency_ms": 150.0},
        {"model_id": "model_a", "quality_score": 95.0, "median_latency_ms": 200.0},
        {"model_id": "model_c", "quality_score": 85.0, "median_latency_ms": 100.0},
    ]
    board = generate_leaderboard(runs)
    assert len(board) == 3
    # model_a is rank 1 (score 95.0)
    assert board[0].model_id == "model_a"
    assert board[0].rank == 1
    # model_c has same score as model_b but lower latency (100 < 150) -> rank 2
    assert board[1].model_id == "model_c"
    assert board[1].rank == 2
    assert board[2].model_id == "model_b"
    assert board[2].rank == 3
