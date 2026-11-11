"""Regression tests for overlapping legacy and versioned API route prefixes."""

from fastapi.testclient import TestClient

from src.evalforge.main import app


def test_api_datasets_uses_versioned_paginated_contract() -> None:
    with TestClient(app) as client:
        response = client.get("/api/datasets?limit=1")
        assert response.status_code == 200
        payload = response.json()
        assert "items" in payload
        assert "total" in payload
        assert "datasets" not in payload


def test_api_v1_datasets_matches_alias_contract() -> None:
    with TestClient(app) as client:
        alias = client.get("/api/datasets?limit=1")
        versioned = client.get("/api/v1/datasets?limit=1")
        assert alias.status_code == versioned.status_code == 200
        assert alias.json().keys() == versioned.json().keys()


def test_api_experiments_keeps_legacy_workflow_contract() -> None:
    with TestClient(app) as client:
        response = client.get("/api/experiments?limit=1")
        assert response.status_code == 200
        payload = response.json()
        assert "experiments" in payload
        assert "items" not in payload


def test_openapi_does_not_advertise_conflicting_dataset_paths() -> None:
    with TestClient(app) as client:
        schema = client.get("/openapi.json").json()
        datasets_paths = [path for path in schema["paths"] if path.rstrip("/") == "/api/datasets"]
        assert len(datasets_paths) == 1
