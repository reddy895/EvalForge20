"""Tests for dataset snapshot and configuration reproducibility metadata."""

import time

from fastapi.testclient import TestClient

from src.evalforge.main import app


def test_run_records_dataset_snapshot_and_fingerprint() -> None:
    with TestClient(app) as client:
        dataset_response = client.post(
            "/api/v1/datasets",
            json={
                "name": f"Reproducibility Dataset {time.time()}",
                "cases": [{"prompt": "Say ok", "expected_output": "ok"}],
            },
        )
        assert dataset_response.status_code == 201
        dataset = dataset_response.json()

        run_response = client.post(
            "/api/v1/evaluations",
            json={
                "dataset_id": dataset["id"],
                "model_id": "mock-reproducibility",
                "provider": "mock",
                "name": "Reproducibility Run",
                "config": {"metrics": ["exact_match"], "temperature": 0.0, "seed": 7},
            },
        )
        assert run_response.status_code == 201
        snapshot = run_response.json()["config_snapshot"]

        assert snapshot["dataset"]["id"] == dataset["id"]
        assert snapshot["dataset"]["version"] == dataset["version"]
        assert len(snapshot["dataset"]["snapshot_hash"]) == 64
        assert snapshot["dataset"]["total_cases"] == 1
        assert snapshot["requested_model_id"] == "mock-reproducibility"
        assert snapshot["evaluators"] == ["exact_match"]
        assert len(snapshot["run_fingerprint"]) == 64


def test_fingerprint_changes_when_seed_changes() -> None:
    with TestClient(app) as client:
        dataset = client.post(
            "/api/v1/datasets",
            json={
                "name": f"Fingerprint Dataset {time.time()}",
                "cases": [{"prompt": "ping", "expected_output": "pong"}],
            },
        ).json()

        fingerprints = []
        for seed in (1, 2):
            response = client.post(
                "/api/v1/evaluations",
                json={
                    "dataset_id": dataset["id"],
                    "model_id": f"mock-fingerprint-{seed}",
                    "provider": "mock",
                    "name": f"Fingerprint Run {seed}",
                    "config": {"metrics": ["exact_match"], "seed": seed},
                },
            )
            assert response.status_code == 201
            fingerprints.append(response.json()["config_snapshot"]["run_fingerprint"])

        assert fingerprints[0] != fingerprints[1]
