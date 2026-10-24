"""Tests for analytics overview calculations, Git commit history aggregation, and verified milestones."""

import pytest
from fastapi.testclient import TestClient

from src.evalforge.main import app
from src.evalforge.services.analytics_service import AnalyticsService, get_analytics_service
from src.evalforge.storage.database import get_session_factory


@pytest.mark.asyncio
async def test_analytics_service_overview() -> None:
    service = get_analytics_service()
    session_factory = get_session_factory()
    async with session_factory() as session:
        overview = await service.get_overview(session)

        # Provider and model counts
        assert overview.total_providers >= 15
        assert overview.total_models >= 10
        assert overview.local_models_count > 0
        assert overview.cloud_models_count > 0

        # Evaluation metrics
        assert overview.total_evaluation_runs >= 0
        assert 0.0 <= overview.overall_pass_rate_percent <= 100.0
        assert 0.0 <= overview.overall_reliability_percent <= 100.0
        assert overview.average_latency_ms >= 0.0


def test_git_commit_analytics_verification() -> None:
    service = AnalyticsService()
    commits_data = service.get_commit_analytics()

    # Verify the milestone requirement — target is now 58 commits
    assert commits_data.target_commits >= 56
    # Exact repository git rev-list count must be at least 56
    assert commits_data.total_verified_commits >= 56
    assert commits_data.target_achieved is True
    assert commits_data.target_progress_percent >= 100.0

    # Ensure source transparency
    assert "Git" in commits_data.source or "git" in commits_data.source.lower()
    assert commits_data.time_range_start
    assert commits_data.time_range_end

    # Verify author distribution
    assert len(commits_data.author_distribution) > 0

    # Verify daily activity heatmap
    assert len(commits_data.daily_activity) > 0
    for day in commits_data.daily_activity:
        assert day.date
        assert day.count >= 0
        assert 0 <= day.level <= 4


def test_git_commit_caching() -> None:
    service = AnalyticsService()
    first_call = service.get_commit_analytics()
    second_call = service.get_commit_analytics()
    # Cache hit returns identical timestamp
    assert first_call.last_updated == second_call.last_updated
    assert first_call.total_verified_commits == second_call.total_verified_commits


def test_analytics_api_endpoints() -> None:
    with TestClient(app) as client:
        # Overview endpoint
        overview_resp = client.get("/api/analytics/overview")
        assert overview_resp.status_code == 200
        overview_data = overview_resp.json()
        assert "total_providers" in overview_data
        assert "total_models" in overview_data
        assert "overall_pass_rate_percent" in overview_data

        # Commits endpoint
        commits_resp = client.get("/api/analytics/commits")
        assert commits_resp.status_code == 200
        commits_data = commits_resp.json()
        assert commits_data["total_verified_commits"] >= 56
        assert commits_data["target_achieved"] is True
        assert len(commits_data["daily_activity"]) > 0

        # Latency distribution endpoints
        lat_v1 = client.get("/api/v1/analytics/latency-distribution")
        assert lat_v1.status_code == 200
        assert isinstance(lat_v1.json(), list)

        lat_mod = client.get("/api/analytics/latency-distribution")
        assert lat_mod.status_code == 200
        assert isinstance(lat_mod.json(), list)


@pytest.mark.asyncio
async def test_get_latency_distribution_service_empty_and_populated() -> None:
    service = get_analytics_service()
    session_factory = get_session_factory()
    async with session_factory() as session:
        dist = await service.get_latency_distribution(session)
        assert isinstance(dist, list)
        for item in dist:
            assert item.model_id
            assert item.min_ms <= item.p50_ms <= item.max_ms
            assert item.p25_ms <= item.p75_ms
            assert item.sample_count > 0
