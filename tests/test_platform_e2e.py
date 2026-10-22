"""End-to-end platform integration tests verifying packaging, routing, and repo integrity."""

from pathlib import Path

from src.evalforge.main import app
from starlette.testclient import TestClient


def test_repository_clean_root_structure() -> None:
    """Verify no symlinks exist at repository root for clean GitHub browsing."""
    repo_root = Path(__file__).resolve().parent.parent
    for artifact in ["alembic.ini", "migrations", "src", "tests_symlink"]:
        target = repo_root / artifact
        assert not target.is_symlink(), f"Expected {artifact} not to be a symlink"

    # Verify real backend directory exists and contains source code
    backend_dir = repo_root / "backend"
    assert backend_dir.is_dir()
    assert (backend_dir / "src" / "evalforge").is_dir()
    assert (backend_dir / "alembic.ini").is_file()
    assert (backend_dir / "migrations").is_dir()
    assert (backend_dir / "tests").is_dir()


def test_platform_health_endpoints() -> None:
    """Verify health endpoints respond with 200 OK across legacy and standard paths."""
    with TestClient(app) as client:
        res = client.get("/health")
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "healthy"
        assert "version" in data

        res_api = client.get("/api/health")
        assert res_api.status_code == 200
        assert res_api.json()["status"] == "healthy"


def test_platform_providers_and_analytics() -> None:
    """Verify provider listing and analytics endpoints resolve correctly."""
    with TestClient(app) as client:
        # Providers catalog
        p_res = client.get("/api/providers")
        assert p_res.status_code == 200
        providers_data = p_res.json()
        assert "providers" in providers_data
        provider_names = [p["name"] for p in providers_data["providers"]]
        assert "ollama" in provider_names

        # Analytics overview
        a_res = client.get("/api/analytics/overview")
        assert a_res.status_code == 200
        overview = a_res.json()
        assert "total_evaluation_runs" in overview

        # Commits
        c_res = client.get("/api/analytics/commits")
        assert c_res.status_code == 200
        commits = c_res.json()
        assert commits["target_achieved"] is True
        assert commits["total_verified_commits"] >= 56



