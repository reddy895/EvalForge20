"""Tests for task-suitability and hardware recommendation engine."""

from backend.app.main import app
from fastapi.testclient import TestClient

client = TestClient(app)


def test_task_recommendation_coding():
    """Verify coding recommendations return ranked models with evidence."""
    resp = client.post(
        "/v1/recommendations/task",
        json={"task": "coding", "prefer_local": True},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "Software Engineering" in data["task"] or "Coding" in data["task"]
    assert len(data["recommendations"]) > 0
    top = data["recommendations"][0]
    assert top["match_score"] >= 50.0
    assert len(top["key_evidence"]) > 0
    assert len(top["important_tradeoffs"]) > 0


def test_hardware_compatibility():
    """Verify hardware profile matching detects memory constraints."""
    resp = client.post(
        "/v1/recommendations/hardware",
        json={"total_ram_gb": 4.0, "has_gpu": False},
    )
    assert resp.status_code == 200
    models = resp.json()
    assert len(models) > 0
    for m in models:
        if m["min_ram_gb"] <= 4.0:
            assert m["can_run_locally"] is True
        else:
            assert m["can_run_locally"] is False
