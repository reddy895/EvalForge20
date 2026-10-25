"""Tests verifying backend startup script, port conflict detection, and CLI argument parsing."""

import subprocess


def test_start_backend_script_dry_run() -> None:
    """Verify that node scripts/start_backend.mjs --dry-run succeeds and logs host/port."""
    res = subprocess.run(
        ["node", "scripts/start_backend.mjs", "--dry-run"],
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert res.returncode == 0
    assert "EvalForge20 — Backend Service Launcher" in res.stdout
    assert "Host: 127.0.0.1" in res.stdout
    assert "Listening URL: http://127.0.0.1:8000" in res.stdout
    assert "Dry run / verification check passed successfully." in res.stdout


def test_start_backend_custom_port_and_host() -> None:
    """Verify that custom CLI arguments override environment variables."""
    res = subprocess.run(
        ["node", "scripts/start_backend.mjs", "--dry-run", "--port", "8085", "--host", "0.0.0.0"],
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert res.returncode == 0
    assert "Host: 0.0.0.0" in res.stdout
    assert "Port: 8085" in res.stdout
    assert "Listening URL: http://0.0.0.0:8085" in res.stdout


def test_port_conflict_detection() -> None:
    """Verify that port conflict is caught and reported with a clean error message."""
    import socket

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        bound_port = s.getsockname()[1]

        res = subprocess.run(
            ["node", "scripts/start_backend.mjs", "--port", str(bound_port)],
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert res.returncode == 1
        assert f"Port {bound_port} is currently in use" in res.stderr

