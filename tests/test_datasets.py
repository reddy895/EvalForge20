"""Unit and API integration tests for Dataset management, JSONL/CSV importers, and export."""

import io
import json
import pytest
from starlette.testclient import TestClient

from src.evalforge.datasets.exporter import export_dataset_to_jsonl
from src.evalforge.datasets.importers.csv_importer import parse_csv_content
from src.evalforge.datasets.importers.jsonl import parse_jsonl_content
from src.evalforge.main import app
from src.evalforge.storage.models.dataset import Dataset, TestCase


def test_parse_jsonl_valid_and_corrupt() -> None:
    raw_content = """
    {"prompt": "What is Python?", "target": "A programming language", "tags": ["coding", "intro"]}
    # This is a comment
    {"input": "What is 2+2?", "answer": "4"}
    {malformed json line}
    {"question": "Valid third question", "ground_truth": "3"}
    {"missing_prompt_key": "some value"}
    """
    valid_cases, errors = parse_jsonl_content(raw_content)

    assert len(valid_cases) == 3
    assert valid_cases[0].prompt == "What is Python?"
    assert valid_cases[0].expected_output == "A programming language"
    assert "coding" in valid_cases[0].tags

    assert valid_cases[1].prompt == "What is 2+2?"
    assert valid_cases[1].expected_output == "4"

    assert valid_cases[2].prompt == "Valid third question"

    assert len(errors) == 2
    assert "Malformed JSON" in errors[0].error
    assert "Missing required 'prompt'" in errors[1].error


def test_parse_csv_and_tsv() -> None:
    csv_content = """prompt,expected_output,tags,extra_col
Calculate square root of 16,4,"math,roots",additional info
Reverse string 'hello',olleh,strings,test
"""
    valid_cases, errors = parse_csv_content(csv_content)
    assert len(valid_cases) == 2
    assert len(errors) == 0
    assert valid_cases[0].prompt == "Calculate square root of 16"
    assert valid_cases[0].expected_output == "4"
    assert "math" in valid_cases[0].tags
    assert valid_cases[0].metadata.get("extra_col") == "additional info"

    # Test TSV format
    tsv_content = "input\ttarget\nTab question 1\tTab answer 1\nTab question 2\tTab answer 2\n"
    tsv_cases, tsv_errors = parse_csv_content(tsv_content)
    assert len(tsv_cases) == 2
    assert len(tsv_errors) == 0
    assert tsv_cases[0].prompt == "Tab question 1"


def test_export_dataset_to_jsonl() -> None:
    ds = Dataset(name="TestDS", version=1)
    ds.tags = ["test"]
    tc1 = TestCase(id="c1", dataset_id="ds1", prompt="Prompt 1", expected_output="Out 1")
    tc1.tags = ["t1"]
    tc2 = TestCase(id="c2", dataset_id="ds1", prompt="Prompt 2", expected_output="Out 2")
    ds.test_cases = [tc1, tc2]

    jsonl_str = export_dataset_to_jsonl(ds)
    lines = [line for line in jsonl_str.splitlines() if line.strip()]
    assert len(lines) == 2

    row1 = json.loads(lines[0])
    assert row1["id"] == "c1"
    assert row1["prompt"] == "Prompt 1"
    assert row1["expected_output"] == "Out 1"


def test_dataset_api_lifecycle() -> None:
    import uuid
    suite_name = f"Integration Suite {uuid.uuid4().hex[:8]}"
    import_name = f"Bulk Imported Suite {uuid.uuid4().hex[:8]}"

    with TestClient(app) as client:
        # 1. Create dataset
        create_payload = {
            "name": suite_name,
            "description": "API verification suite",
            "tags": ["core", "smoke"],
            "cases": [
                {
                    "prompt": "Write a python function to add two numbers.",
                    "expected_output": "def add(a, b): return a + b",
                    "tags": ["python", "math"],
                }
            ],
        }
        res = client.post("/api/v1/datasets", json=create_payload)
        assert res.status_code == 201
        created_data = res.json()
        dataset_id = created_data["id"]
        assert created_data["name"] == suite_name
        assert created_data["case_count"] == 1
        assert len(created_data["cases"]) == 1

        # 2. Add more cases
        cases_payload = [
            {
                "prompt": "What is the capital of France?",
                "expected_output": "Paris",
                "tags": ["geography"],
            }
        ]
        res = client.post(f"/api/v1/datasets/{dataset_id}/cases", json=cases_payload)
        assert res.status_code == 201
        assert len(res.json()) == 1

        # 3. Retrieve dataset details
        res = client.get(f"/api/v1/datasets/{dataset_id}")
        assert res.status_code == 200
        detail = res.json()
        assert detail["case_count"] == 2
        assert len(detail["cases"]) == 2

        # 4. Patch dataset
        patch_res = client.patch(
            f"/api/v1/datasets/{dataset_id}",
            json={"description": "Updated suite description"},
        )
        assert patch_res.status_code == 200
        assert patch_res.json()["description"] == "Updated suite description"
        assert patch_res.json()["version"] >= 2

        # 5. Export dataset
        export_res = client.get(f"/api/v1/datasets/{dataset_id}/export")
        assert export_res.status_code == 200
        export_lines = [line for line in export_res.text.splitlines() if line.strip()]
        assert len(export_lines) == 2

        # 6. Test multipart import
        file_bytes = b'{"prompt": "Imported Q1", "target": "A1"}\n{"prompt": "Imported Q2", "target": "A2"}'
        import_res = client.post(
            "/api/v1/datasets/import",
            data={"name": import_name, "format": "jsonl"},
            files={"file": ("dataset.jsonl", io.BytesIO(file_bytes), "application/jsonl")},
        )
        assert import_res.status_code == 201
        import_data = import_res.json()
        assert import_data["imported_cases"] == 2
        assert import_data["failed_rows"] == 0

        # 7. Delete dataset
        del_res = client.delete(f"/api/v1/datasets/{dataset_id}")
        assert del_res.status_code == 204

        # 8. Confirm deleted
        check_del = client.get(f"/api/v1/datasets/{dataset_id}")
        assert check_del.status_code == 404
