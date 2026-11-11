"""Tests for dataset and evaluation sorting contracts."""

import time

from fastapi.testclient import TestClient

from src.evalforge.main import app


def test_datasets_can_be_sorted_by_name() -> None:
    with TestClient(app) as client:
        stamp = time.time()
        for name in ("zeta-sort", "alpha-sort", "middle-sort"):
            response = client.post(
                "/api/v1/datasets",
                json={
                    "name": f"{name}-{stamp}",
                    "cases": [{"prompt": "x", "expected_output": "x"}],
                },
            )
            assert response.status_code == 201

        response = client.get(
            "/api/v1/datasets",
            params={"sort_by": "name", "sort_order": "asc", "limit": 100},
        )
        assert response.status_code == 200
        names = [item["name"] for item in response.json()["items"]]
        matching = [name for name in names if name.endswith(str(stamp))]
        assert matching == sorted(matching)


def test_invalid_dataset_sort_field_is_rejected() -> None:
    with TestClient(app) as client:
        response = client.get("/api/v1/datasets", params={"sort_by": "drop_table"})
        assert response.status_code == 422


def test_evaluations_can_be_sorted_by_model_id() -> None:
    with TestClient(app) as client:
        dataset = client.post(
            "/api/v1/datasets",
            json={
                "name": f"Sorting Dataset {time.time()}",
                "cases": [{"prompt": "x", "expected_output": "x"}],
            },
        ).json()

        for model in ("mock-sort-z", "mock-sort-a"):
            response = client.post(
                "/api/v1/evaluations",
                json={
                    "dataset_id": dataset["id"],
                    "model_id": model,
                    "provider": "mock",
                    "name": f"Sort {model}",
                    "config": {"metrics": ["exact_match"]},
                },
            )
            assert response.status_code == 201

        response = client.get(
            "/api/v1/evaluations",
            params={
                "dataset_id": dataset["id"],
                "sort_by": "model_id",
                "sort_order": "asc",
            },
        )
        assert response.status_code == 200
        models = [item["model_id"] for item in response.json()["items"]]
        assert models == sorted(models)


def test_invalid_evaluation_sort_order_is_rejected() -> None:
    with TestClient(app) as client:
        response = client.get("/api/v1/evaluations", params={"sort_order": "sideways"})
        assert response.status_code == 422
