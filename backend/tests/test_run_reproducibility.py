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


def test_compare_marks_models_compatible_when_data_and_config_match() -> None:
    with TestClient(app) as client:
        dataset = client.post(
            "/api/v1/datasets",
            json={
                "name": f"Compare Dataset {time.time()}",
                "cases": [{"prompt": "a", "expected_output": "a"}],
            },
        ).json()

        run_ids = []
        for model in ("mock-compare-a", "mock-compare-b"):
            response = client.post(
                "/api/v1/evaluations",
                json={
                    "dataset_id": dataset["id"],
                    "model_id": model,
                    "provider": "mock",
                    "name": f"Compare {model}",
                    "config": {"metrics": ["exact_match"], "seed": 11},
                },
            )
            assert response.status_code == 201
            run_ids.append(response.json()["id"])

        comparison = client.get("/api/v1/evaluations/compare", params={"ids": run_ids})
        assert comparison.status_code == 200
        payload = comparison.json()
        assert payload["all_compatible"] is True
        assert len(payload["runs"]) == 2
        assert payload["compatibility"][0]["model_id"] == "mock-compare-a"
        assert payload["compatibility"][1]["differences"] == []
        assert payload["deltas_from"] == run_ids[0]


def test_compare_reports_configuration_differences() -> None:
    with TestClient(app) as client:
        dataset = client.post(
            "/api/v1/datasets",
            json={
                "name": f"Compare Diff Dataset {time.time()}",
                "cases": [{"prompt": "b", "expected_output": "b"}],
            },
        ).json()

        run_ids = []
        for seed in (1, 2):
            response = client.post(
                "/api/v1/evaluations",
                json={
                    "dataset_id": dataset["id"],
                    "model_id": f"mock-compare-seed-{seed}",
                    "provider": "mock",
                    "name": f"Compare seed {seed}",
                    "config": {"metrics": ["exact_match"], "seed": seed},
                },
            )
            run_ids.append(response.json()["id"])

        payload = client.get(
            "/api/v1/evaluations/compare", params={"ids": run_ids}
        ).json()
        assert payload["all_compatible"] is False
        assert "configuration_differs" in payload["compatibility"][1]["differences"]
