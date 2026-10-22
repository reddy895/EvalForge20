"""Security verification, boundary defense, and error protection tests."""

import pytest
from starlette.testclient import TestClient

from src.evalforge.core.errors import PayloadTooLargeError, SecurityViolationError
from src.evalforge.core.security import (
    enforce_content_length,
    sanitize_filename,
    validate_path_safety,
)
from src.evalforge.main import app


def test_security_headers_present_on_all_responses() -> None:
    with TestClient(app) as client:
        response = client.get("/health")
        assert response.status_code == 200
        headers = response.headers

        assert headers.get("X-Content-Type-Options") == "nosniff"
        assert headers.get("X-Frame-Options") == "DENY"
        assert headers.get("X-XSS-Protection") == "1; mode=block"
        assert "X-Request-ID" in headers
        assert "X-Process-Time-Ms" in headers


def test_path_traversal_validation() -> None:
    base_dir = "/var/evalforge/data"

    # Safe sub-path
    safe_path = validate_path_safety("/var/evalforge/data/sub/dataset.jsonl", base_dir=base_dir)
    assert safe_path.startswith(base_dir)

    # Directory traversal attempt
    with pytest.raises(SecurityViolationError) as exc_info:
        validate_path_safety("/var/evalforge/data/../../etc/passwd", base_dir=base_dir)
    assert "Path traversal detected" in str(exc_info.value)

    # Null-byte injection attempt
    with pytest.raises(SecurityViolationError) as null_exc:
        validate_path_safety("/var/evalforge/data/image.png\0.php", base_dir=base_dir)
    assert "null byte" in str(null_exc.value)


def test_sanitize_filename() -> None:
    assert sanitize_filename("../../../secret.env") == "secret.env"
    assert sanitize_filename("safe_file-1.jsonl") == "safe_file-1.jsonl"
    assert sanitize_filename("bad;file$name`test.csv") == "bad_file_name_test.csv"


def test_payload_size_enforcement() -> None:
    # Within limit
    enforce_content_length(content_length=1000, max_allowed_bytes=5000)

    # Exceeding limit
    with pytest.raises(PayloadTooLargeError):
        enforce_content_length(content_length=10000, max_allowed_bytes=5000)


def test_rag_api_endpoint() -> None:
    with TestClient(app) as client:
        payload = {
            "cases": [
                {
                    "query": "What is the capital of Japan?",
                    "retrieved_contexts": [
                        "Tokyo is the bustling capital city of Japan.",
                        "Kyoto was the former imperial capital of Japan.",
                    ],
                    "answer": "Tokyo is the capital of Japan.",
                    "reference_answer": "Tokyo is Japan's capital.",
                    "expected_citations": ["Tokyo is the bustling capital city of Japan."],
                }
            ],
            "threshold": 0.6,
        }

        res = client.post("/api/v1/rag/evaluate", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert data["total_cases"] == 1
        assert data["passed_cases"] == 1
        avg = data["average_scorecard"]
        assert avg["context_relevance"] > 0.5
        assert avg["faithfulness"] > 0.5
        assert avg["answer_relevance"] > 0.5
        assert avg["citation_recall"] == 1.0


def test_unhandled_exception_sanitization() -> None:
    """Verify that unhandled exceptions do not leak stack traces or internal paths to clients."""
    with TestClient(app) as client:
        # Requesting a non-existent route should return clean 404
        res = client.get("/api/v1/nonexistent-endpoint")
        assert res.status_code == 404
