"""Unit and integration tests for Evaluation runner engine, lifecycle, and cancellation."""

import asyncio
import time
import uuid
import pytest
from starlette.testclient import TestClient

from src.evalforge.experiments.case_runner import CaseRunner
from src.evalforge.experiments.concurrency import BoundedConcurrencyPool
from src.evalforge.experiments.snapshot import FrozenTestCase, create_dataset_snapshot
from src.evalforge.main import app
from src.evalforge.providers.mock import MockProvider
from src.evalforge.schemas.evaluation import EvaluationConfig
from src.evalforge.storage.models.dataset import Dataset, TestCase


@pytest.mark.asyncio
async def test_dataset_snapshot_immutability() -> None:
    ds = Dataset(name="Snapshot Test", version=1)
    ds.tags = ["freeze"]
    tc = TestCase(id="tc-1", dataset_id="ds-1", prompt="Initial prompt", expected_output="Initial target")
    ds.test_cases = [tc]

    snapshot = create_dataset_snapshot(ds)
    assert snapshot.total_cases == 1
    assert snapshot.cases[0].prompt == "Initial prompt"
    initial_hash = snapshot.snapshot_hash

    # Mutate original ORM model
    tc.prompt = "Mutated prompt"
    assert snapshot.cases[0].prompt == "Initial prompt"  # Frozen snapshot remains unchanged!

    # A new snapshot has a different hash
    new_snapshot = create_dataset_snapshot(ds)
    assert new_snapshot.snapshot_hash != initial_hash


@pytest.mark.asyncio
async def test_bounded_concurrency_pool() -> None:
    pool = BoundedConcurrencyPool(max_concurrency=2)
    max_active = 0
    active = 0

    async def worker(item: int) -> int:
        nonlocal active, max_active
        active += 1
        if active > max_active:
            max_active = active
        await asyncio.sleep(0.02)
        active -= 1
        return item * 2

    results = await pool.map(worker, [1, 2, 3, 4, 5])
    assert len(results) == 5
    assert set(results) == {2, 4, 6, 8, 10}
    assert max_active <= 2  # Bounded to concurrency limit


@pytest.mark.asyncio
async def test_case_runner_execution() -> None:
    mock_p = MockProvider(
        canned_responses={"capital": "Paris", "add": "4"}
    )
    config = EvaluationConfig(metrics=["exact_match", "token_f1"])
    runner = CaseRunner(provider=mock_p, model_id="mock-llama-3.1-8b", config=config)

    case = FrozenTestCase(
        id="case-1",
        prompt="What is the capital of France?",
        expected_output="Paris",
    )
    result = await runner.execute_case(case, evaluation_id="eval-1")

    assert result.passed is True
    assert result.actual_output == "Paris"
    assert "exact_match" in result.metrics
    assert result.metrics["exact_match"]["score"] == 1.0


def test_full_evaluation_api_lifecycle() -> None:
    unique_suffix = uuid.uuid4().hex[:8]
    with TestClient(app) as client:
        # 1. Create dataset
        ds_res = client.post(
            "/api/v1/datasets",
            json={
                "name": f"Eval Test Suite {unique_suffix}",
                "description": "Lifecycle testing suite",
                "cases": [
                    {
                        "prompt": "What is the capital of France?",
                        "expected_output": "Mock response for: What is the capital of France?",
                    },
                    {
                        "prompt": "What is 2 + 2?",
                        "expected_output": "Mock response for: What is 2 + 2?",
                    },
                ],
            },
        )
        assert ds_res.status_code == 201
        dataset_id = ds_res.json()["id"]

        # 2. Launch evaluation with mock provider
        eval_res = client.post(
            "/api/v1/evaluations",
            json={
                "name": f"Mock Run {unique_suffix}",
                "model_id": "mock-llama-3.1-8b",
                "provider": "mock",
                "dataset_id": dataset_id,
                "config": {
                    "metrics": ["exact_match", "token_f1"],
                    "concurrency": 2,
                },
            },
        )
        assert eval_res.status_code == 201
        eval_id = eval_res.json()["id"]

        # 3. Wait for background task to complete
        status_val = "running"
        for _ in range(50):
            time.sleep(0.05)
            poll_res = client.get(f"/api/v1/evaluations/{eval_id}")
            assert poll_res.status_code == 200
            status_val = poll_res.json()["status"]
            if status_val in ("completed", "failed"):
                break

        assert status_val == "completed"

        # 4. Inspect results
        results_res = client.get(f"/api/v1/evaluations/{eval_id}/results")
        assert results_res.status_code == 200
        detail = results_res.json()
        assert detail["status"] == "completed"
        assert detail["total_cases"] == 2
        assert detail["completed_cases"] == 2
        assert detail["pass_rate"] == 1.0
        assert len(detail["results"]) == 2
        assert detail["results"][0]["passed"] is True
        assert "exact_match" in detail["results"][0]["metrics"]


def test_evaluation_cancellation_flow() -> None:
    unique_suffix = uuid.uuid4().hex[:8]
    with TestClient(app) as client:
        # Create dataset with multiple cases
        ds_res = client.post(
            "/api/v1/datasets",
            json={
                "name": f"Cancel Test Suite {unique_suffix}",
                "cases": [
                    {"prompt": f"Slow task {i}", "expected_output": "done"}
                    for i in range(10)
                ],
            },
        )
        dataset_id = ds_res.json()["id"]

        # Launch evaluation
        eval_res = client.post(
            "/api/v1/evaluations",
            json={
                "name": f"Cancel Run {unique_suffix}",
                "model_id": "mock-llama-3.1-8b",
                "provider": "mock",
                "dataset_id": dataset_id,
                "config": {"concurrency": 1},
            },
        )
        eval_id = eval_res.json()["id"]

        # Immediately cancel
        cancel_res = client.post(f"/api/v1/evaluations/{eval_id}/cancel")
        assert cancel_res.status_code == 200
        assert cancel_res.json()["status"] == "cancelled"
