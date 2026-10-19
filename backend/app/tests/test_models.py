"""Tests for model catalog and profile retrieval."""

from backend.app.main import app
from fastapi.testclient import TestClient

client = TestClient(app)


def test_list_models():
    """Verify catalog returns curated models with summary attributes."""
    resp = client.get("/v1/models")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 8
    first = data[0]
    assert "id" in first
    assert "name" in first
    assert "hardware_min_ram_gb" in first
    assert "recommended_tasks" in first


def test_search_and_filter_models():
    """Verify search and provider filtering."""
    resp = client.get("/v1/models?query=qwen")
    assert resp.status_code == 200
    data = resp.json()
    assert all("qwen" in m["name"].lower() or "qwen" in m["model_identifier"].lower() for m in data)

    resp_task = client.get("/v1/models?task=coding")
    assert resp_task.status_code == 200
    assert len(resp_task.json()) > 0


def test_get_model_profile_success():
    """Verify complete profile with hardware, strengths, and benchmarks."""
    resp = client.get("/v1/models/qwen-2.5-3b-instruct")
    assert resp.status_code == 200
    p = resp.json()
    assert p["name"] == "Qwen 2.5 3B Instruct"
    assert p["context_window"] == 32768
    assert len(p["benchmarks"]) >= 1
    assert p["hardware"]["min_ram_gb"] > 0
    assert len(p["strengths"]) > 0


def test_get_model_profile_not_found():
    """Verify 404 on nonexistent model."""
    resp = client.get("/v1/models/nonexistent-model-xyz")
    assert resp.status_code == 404


def test_mistral_catalog_and_profile():
    """Verify Mistral 7B and NeMo 12B exist with verified Apache 2.0 license."""
    resp = client.get("/v1/models?query=mistral")
    assert resp.status_code == 200
    models = resp.json()
    assert len(models) >= 2
    ids = [m["id"] for m in models]
    assert "mistral-7b-instruct-v0.3" in ids
    assert "mistral-nemo-12b-instruct" in ids

    profile_resp = client.get("/v1/models/mistral-7b-instruct-v0.3")
    assert profile_resp.status_code == 200
    p = profile_resp.json()
    assert p["provider"] == "Mistral AI"
    assert p["license"] == "Apache 2.0"
    assert p["supports_tools"] is True
    assert any(b["benchmark_name"] == "MMLU" for b in p["benchmarks"])


def test_gemini_catalog_and_profile():
    """Verify Gemini 1.5 Flash and Pro exist with 1M+ context window."""
    resp = client.get("/v1/models?query=gemini")
    assert resp.status_code == 200
    models = resp.json()
    assert len(models) >= 2
    ids = [m["id"] for m in models]
    assert "gemini-1-5-flash" in ids
    assert "gemini-1-5-pro" in ids

    profile_resp = client.get("/v1/models/gemini-1-5-pro")
    assert profile_resp.status_code == 200
    p = profile_resp.json()
    assert p["provider"] == "Google"
    assert p["context_window"] == 2097152
    assert p["is_local"] is False
    assert any(b["benchmark_name"] == "GSM8K" for b in p["benchmarks"])


