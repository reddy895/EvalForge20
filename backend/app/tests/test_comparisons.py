"""Tests for multi-model side-by-side comparison service."""

from backend.app.main import app
from fastapi.testclient import TestClient

client = TestClient(app)


def test_compare_models():
    """Verify side-by-side comparison matrix across 2 models."""
    resp = client.post(
        "/v1/comparisons",
        json={"model_ids": ["qwen-2.5-3b-instruct", "llama-3.2-3b-instruct"]},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["compared_models"]) == 2
    assert len(data["matrix"]) >= 8
    assert "summary_verdict" in data
    assert len(data["comparability_notes"]) > 0
