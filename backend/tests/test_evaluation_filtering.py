"""Unit and API integration tests for evaluation list filtering, pagination, and total count."""

import pytest
from fastapi.testclient import TestClient

from src.evalforge.main import app
from src.evalforge.storage.database import get_session_factory
from src.evalforge.storage.models.evaluation import EvaluationRun


@pytest.mark.asyncio
async def test_list_evaluations_filtering_and_pagination():
    session_factory = get_session_factory()
    async with session_factory() as session:
        # Seed 3 runs with different models and statuses
        run1 = EvaluationRun(
            name="Filter Run 1",
            model_id="filter-model-a",
            provider="mock",
            status="completed",
            total_cases=5,
        )
        run2 = EvaluationRun(
            name="Filter Run 2",
            model_id="filter-model-b",
            provider="mock",
            status="completed",
            total_cases=5,
        )
        run3 = EvaluationRun(
            name="Filter Run 3",
            model_id="filter-model-a",
            provider="mock",
            status="failed",
            total_cases=5,
        )
        session.add_all([run1, run2, run3])
        await session.commit()

    with TestClient(app) as client:
        # 1. Test filtering by model_id
        res_model = client.get("/api/v1/evaluations?model_id=filter-model-a")
        assert res_model.status_code == 200
        data_model = res_model.json()
        assert data_model["total"] >= 2
        assert all(item["model_id"] == "filter-model-a" for item in data_model["items"])

        # 2. Test filtering by status
        res_status = client.get("/api/v1/evaluations?model_id=filter-model-a&status=failed")
        assert res_status.status_code == 200
        data_status = res_status.json()
        assert data_status["total"] >= 1
        assert all(item["status"] == "failed" for item in data_status["items"])

        # 3. Test pagination limit
        res_limit = client.get("/api/v1/evaluations?limit=1")
        assert res_limit.status_code == 200
        data_limit = res_limit.json()
        assert len(data_limit["items"]) == 1
        assert data_limit["total"] >= 3
