"""Unit and integration tests for Evaluation runner engine, lifecycle, and cancellation."""

import asyncio
import time
import uuid

import pytest
from fastapi.testclient import TestClient

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
    tc = TestCase(
        id="tc-1", dataset_id="ds-1", prompt="Initial prompt", expected_output="Initial target"
    )
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
    mock_p = MockProvider(canned_responses={"capital": "Paris", "add": "4"})
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
                    {"prompt": f"Slow task {i}", "expected_output": "done"} for i in range(10)
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


def test_multi_model_distinct_evaluations_via_api() -> None:
    """Verifies that two different models evaluated on the same dataset produce strictly isolated runs."""
    unique_suffix = uuid.uuid4().hex[:8]
    with TestClient(app) as client:
        # Create dataset
        ds_res = client.post(
            "/api/v1/datasets",
            json={
                "name": f"Multi-Model Suite {unique_suffix}",
                "cases": [
                    {"prompt": "Say hello", "expected_output": "hello"},
                    {"prompt": "Say goodbye", "expected_output": "goodbye"},
                ],
            },
        )
        assert ds_res.status_code == 201
        dataset_id = ds_res.json()["id"]

        # Run 1: Model A
        run_a_res = client.post(
            "/api/v1/evaluations",
            json={
                "name": f"Run Model A {unique_suffix}",
                "model_id": "mock-llama-3.1-8b",
                "provider": "mock",
                "dataset_id": dataset_id,
            },
        )
        assert run_a_res.status_code == 201
        run_a_id = run_a_res.json()["id"]

        # Run 2: Model B
        run_b_res = client.post(
            "/api/v1/evaluations",
            json={
                "name": f"Run Model B {unique_suffix}",
                "model_id": "mock-qwen-2.5-7b",
                "provider": "mock",
                "dataset_id": dataset_id,
            },
        )
        assert run_b_res.status_code == 201
        run_b_id = run_b_res.json()["id"]

        # Verify distinct identities
        assert run_a_id != run_b_id

        # Poll Run A
        for _ in range(50):
            time.sleep(0.05)
            poll_a = client.get(f"/api/v1/evaluations/{run_a_id}").json()
            if poll_a["status"] in ("completed", "failed"):
                break

        # Poll Run B
        for _ in range(50):
            time.sleep(0.05)
            poll_b = client.get(f"/api/v1/evaluations/{run_b_id}").json()
            if poll_b["status"] in ("completed", "failed"):
                break

        assert poll_a["model_id"] == "mock-llama-3.1-8b"
        assert poll_b["model_id"] == "mock-qwen-2.5-7b"

        # Check detail results
        det_a = client.get(f"/api/v1/evaluations/{run_a_id}/results").json()
        det_b = client.get(f"/api/v1/evaluations/{run_b_id}/results").json()

        assert det_a["id"] == run_a_id
        assert det_b["id"] == run_b_id
        assert det_a["model_id"] != det_b["model_id"]
        assert len(det_a["results"]) == 2
        assert len(det_b["results"]) == 2


@pytest.mark.asyncio
async def test_evaluation_engine_marks_failed_status_when_all_cases_drop_connection() -> None:
    """When all cases encounter provider network failure, run status becomes 'failed' and pass_rate is null."""
    from unittest.mock import AsyncMock, MagicMock
    from src.evalforge.providers.base import BaseProvider
    from src.evalforge.providers.registry import get_provider_registry
    from src.evalforge.services.evaluation_service import EvaluationService
    from src.evalforge.storage.database import get_session_factory
    from src.evalforge.storage.models.evaluation import EvaluationRun
    from src.evalforge.storage.repositories.evaluation_repo import EvaluationRepository

    class FailingProvider(BaseProvider):
        def __init__(self) -> None:
            super().__init__(name="failing_test_provider", display_name="Failing Provider")

        async def generate(self, request: Any) -> Any:
            raise ConnectionRefusedError("Could not connect to model daemon at 127.0.0.1:11434")

        async def health_check(self) -> bool:
            return False

        async def list_models(self) -> list[Any]:
            return []

        async def get_model_capabilities(self, model_id: str) -> Any:
            return None

    # Register provider
    reg = get_provider_registry()
    fail_prov = FailingProvider()
    reg.register("failing_test_provider", fail_prov)

    # Setup snapshot with 2 cases
    tc1 = FrozenTestCase(id="c1", prompt="Prompt 1", expected_output="Expected 1")
    tc2 = FrozenTestCase(id="c2", prompt="Prompt 2", expected_output="Expected 2")
    snapshot = create_dataset_snapshot(Dataset(name="Failure Test", version=1))
    snapshot.cases = [tc1, tc2]

    # Create run record
    session_factory = get_session_factory()
    run_id = f"test-fail-{uuid.uuid4().hex[:8]}"
    async with session_factory() as session:
        repo = EvaluationRepository(session)
        run = EvaluationRun(
            id=run_id,
            name="Failing Network Test Run",
            model_id="failing-model",
            provider="failing_test_provider",
            status="queued",
            total_cases=2,
        )
        await repo.add(run)
        await session.commit()

    # Execute background task
    cfg = EvaluationConfig(metrics=["exact_match"], concurrency=1)
    await EvaluationService._execute_evaluation_task(
        run_id, snapshot, "failing-model", "failing_test_provider", cfg
    )

    # Verify run state in database
    async with session_factory() as session:
        repo = EvaluationRepository(session)
        finished_run = await repo.get(run_id)
        assert finished_run is not None
        assert finished_run.status == "failed"
        assert finished_run.pass_rate is None  # Must NOT be 0.0 synthetic score
        assert finished_run.avg_latency_ms is None
        assert finished_run.error_message is not None
        assert "inference error" in finished_run.error_message.lower() or "timeout" in finished_run.error_message.lower()

