"""Unit test suite for deterministic evaluators and multi-format dataset loaders."""

import pytest
from app.domain.contracts import EvaluatorInput
from app.domain.dataset import DatasetVersion
from app.domain.models import EvaluationCase
from app.evaluators.code.classification import ClassificationAccuracyEvaluator
from app.evaluators.code.contains_match import ContainsMatchEvaluator
from app.evaluators.code.exact_match import ExactMatchEvaluator
from app.evaluators.code.json_schema import JSONSchemaEvaluator
from app.evaluators.code.normalized_match import NormalizedMatchEvaluator
from app.evaluators.code.task_assertions import TaskAssertionEvaluator
from app.evaluators.code.token_f1 import TokenF1Evaluator


@pytest.mark.asyncio
async def test_exact_match_evaluator():
    evaluator = ExactMatchEvaluator()

    # Success case
    case = EvaluationCase(id="1", input="What is 2+2?", expected_output="4")
    res = await evaluator.evaluate(EvaluatorInput(case=case, actual_output="4"))
    assert res.passed is True
    assert res.score == 1.0

    # Failure case
    res2 = await evaluator.evaluate(EvaluatorInput(case=case, actual_output=" 4 "))
    assert res2.passed is False
    assert res2.score == 0.0


@pytest.mark.asyncio
async def test_normalized_match_evaluator():
    evaluator = NormalizedMatchEvaluator()
    case = EvaluationCase(id="2", input="Capital of UK?", expected_output="London")

    res = await evaluator.evaluate(EvaluatorInput(case=case, actual_output="  london!  "))
    assert res.passed is True
    assert res.score == 1.0


@pytest.mark.asyncio
async def test_contains_match_evaluator():
    evaluator = ContainsMatchEvaluator()
    case = EvaluationCase(id="3", input="Explain photosynthesis", expected_output="chlorophyll")

    # Found case
    res = await evaluator.evaluate(
        EvaluatorInput(
            case=case,
            actual_output="Plants absorb sunlight using chlorophyll in their leaves.",
        )
    )
    assert res.passed is True
    assert res.score == 1.0

    # Missing case
    res2 = await evaluator.evaluate(
        EvaluatorInput(case=case, actual_output="Plants absorb sunlight and water.")
    )
    assert res2.passed is False
    assert res2.score == 0.0


@pytest.mark.asyncio
async def test_classification_accuracy_evaluator():
    evaluator = ClassificationAccuracyEvaluator()
    case = EvaluationCase(
        id="4",
        input="Sentiment of: Great job!",
        expected_output="positive",
        category="classification",
    )

    res = await evaluator.evaluate(
        EvaluatorInput(case=case, actual_output="The classification is: **positive**.")
    )
    assert res.passed is True
    assert res.score == 1.0

    res2 = await evaluator.evaluate(EvaluatorInput(case=case, actual_output="negative"))
    assert res2.passed is False
    assert res2.score == 0.0


@pytest.mark.asyncio
async def test_token_f1_evaluator():
    evaluator = TokenF1Evaluator()
    case = EvaluationCase(id="5", input="Translate", expected_output="the quick brown fox jumps")

    # Partial overlap
    res = await evaluator.evaluate(
        EvaluatorInput(case=case, actual_output="the fast brown fox jumps")
    )
    assert res.passed is True
    assert res.score is not None and res.score > 0.7


@pytest.mark.asyncio
async def test_json_schema_evaluator():
    evaluator = JSONSchemaEvaluator()
    schema = {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "age": {"type": "integer"},
        },
        "required": ["name", "age"],
    }
    case = EvaluationCase(id="6", input="Generate user JSON", metadata={"schema": schema})

    # Valid JSON matching schema
    res = await evaluator.evaluate(
        EvaluatorInput(case=case, actual_output='{"name": "Alice", "age": 30}')
    )
    assert res.passed is True
    assert res.score == 1.0

    # Invalid JSON schema (missing age, wrong type)
    res2 = await evaluator.evaluate(
        EvaluatorInput(case=case, actual_output='{"name": "Alice", "age": "thirty"}')
    )
    assert res2.passed is False
    assert res2.score == 0.0
    assert "violations" in res2.details


@pytest.mark.asyncio
async def test_task_assertion_evaluator():
    evaluator = TaskAssertionEvaluator()
    assertions = [
        {"type": "contains_all", "value": ["revenue", "profit"]},
        {"type": "not_contains", "value": ["error", "confidential"]},
        {"type": "numeric_range", "min": 100, "max": 200},
        {"type": "json_field_equals", "field": "status", "expected": "ok"},
    ]
    case = EvaluationCase(id="7", input="Report", metadata={"assertions": assertions})

    output_text = """
    Here is the report:
    revenue grew and profit increased to 150 million.
    ```json
    {"status": "ok", "items": 150}
    ```
    """
    res = await evaluator.evaluate(EvaluatorInput(case=case, actual_output=output_text))
    assert res.passed is True
    assert res.score == 1.0


def test_dataset_version_multi_format_parsing():
    # JSONL parsing
    jsonl_str = '{"id": "c1", "input": "prompt 1", "expected_output": "out 1", "category": "reasoning", "metadata": {"complexity": "low"}}\n'
    ds_jsonl = DatasetVersion.from_jsonl_content("test-ds", jsonl_str)
    assert len(ds_jsonl.cases) == 1
    assert ds_jsonl.stats.total_cases == 1
    assert ds_jsonl.stats.complexity_distribution.get("low") == 1

    # JSON Array parsing
    json_str = '[{"id": "c2", "input": "prompt 2", "expected_output": "out 2", "category": "coding", "metadata": {"complexity": "high"}}]'
    ds_json = DatasetVersion.from_json_content("test-ds", json_str)
    assert len(ds_json.cases) == 1
    assert ds_json.stats.complexity_distribution.get("high") == 1

    # CSV parsing
    csv_str = "id,input,expected_output,category,tags,complexity\nc3,csv prompt,csv output,math,tag1,medium\n"
    ds_csv = DatasetVersion.from_csv_content("test-ds", csv_str)
    assert len(ds_csv.cases) == 1
    assert ds_csv.cases[0].input == "csv prompt"
    assert ds_csv.stats.complexity_distribution.get("medium") == 1
