"""API tests for dataset preview, pagination, integrity, duplication, and imports."""

import json
import uuid

from fastapi.testclient import TestClient

from src.evalforge.main import app


def _create_dataset(client: TestClient, name: str, cases: list[dict]) -> dict:
    response = client.post(
        "/api/v1/datasets",
        json={"name": name, "description": "test dataset", "tags": ["test"], "cases": cases},
    )
    assert response.status_code == 201, response.text
    return response.json()


def test_dataset_preview_pagination_integrity_and_duplicate() -> None:
    suffix = uuid.uuid4().hex[:8]
    name = f"lifecycle-{suffix}"
    cases = [
        {"prompt": f"Question {i}", "expected_output": f"Answer {i}"} for i in range(7)
    ]
    with TestClient(app) as client:
        created = _create_dataset(client, name, cases)
        dataset_id = created["id"]

        preview = client.get(f"/api/v1/datasets/{dataset_id}/preview?limit=3")
        assert preview.status_code == 200
        body = preview.json()
        assert body["total_cases"] == 7
        assert len(body["items"]) == 3

        page = client.get(f"/api/v1/datasets/{dataset_id}/cases?offset=5&limit=2")
        assert page.status_code == 200
        page_body = page.json()
        assert page_body["total"] == 7
        assert len(page_body["items"]) == 2

        integrity = client.get(f"/api/v1/datasets/{dataset_id}/integrity")
        assert integrity.status_code == 200
        report = integrity.json()
        assert report["case_count"] == 7
        assert report["is_valid"] is True
        assert report["duplicate_prompts"] == 0
        assert len(report["fingerprint"]) == 64

        clone = client.post(f"/api/v1/datasets/{dataset_id}/duplicate?new_name={name}-copy")
        assert clone.status_code == 201, clone.text
        clone_id = clone.json()["id"]
        assert clone_id != dataset_id

        clone_cases = client.get(f"/api/v1/datasets/{clone_id}/cases?limit=100").json()
        assert clone_cases["total"] == 7

        first_case_id = clone_cases["items"][0]["id"]
        deleted = client.delete(f"/api/v1/datasets/{clone_id}/cases/{first_case_id}")
        assert deleted.status_code == 204
        remaining = client.get(f"/api/v1/datasets/{clone_id}/cases?limit=100").json()
        assert remaining["total"] == 6


def test_dataset_import_rejects_invalid_utf8() -> None:
    suffix = uuid.uuid4().hex[:8]
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/datasets/import",
            data={"name": f"bad-utf8-{suffix}", "format": "jsonl"},
            files={"file": ("data.jsonl", b"\xff\xfe\x00bad", "application/jsonl")},
        )
        assert response.status_code == 422
        assert response.json()["error"]["code"] == "VALIDATION_FAILED"


def test_dataset_import_reports_duplicates() -> None:
    suffix = uuid.uuid4().hex[:8]
    rows = [
        {"prompt": "Same", "expected_output": "Answer"},
        {"prompt": "Same", "expected_output": "Answer"},
        {"prompt": "Different", "expected_output": "Answer"},
    ]
    content = "\n".join(json.dumps(row) for row in rows).encode()
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/datasets/import",
            data={"name": f"dedupe-{suffix}", "format": "jsonl"},
            files={"file": ("data.jsonl", content, "application/jsonl")},
        )
        assert response.status_code == 201, response.text
        body = response.json()
        assert body["imported_cases"] == 2
        assert body["duplicates_skipped"] == 1
        assert body["warnings"]
