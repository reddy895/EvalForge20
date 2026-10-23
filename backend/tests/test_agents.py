"""Unit and integration test suite for Agent tool harness, safety, and trace auditing."""

import uuid

import pytest
from fastapi.testclient import TestClient

from src.evalforge.agents.agent_metrics import compute_agent_metrics
from src.evalforge.agents.tool_harness import SafeToolHarness, safe_eval_math
from src.evalforge.main import app
from src.evalforge.schemas.agent import AgentStepTrace


def test_safe_math_ast_evaluator() -> None:
    assert safe_eval_math("2 + 2") == 4.0
    assert safe_eval_math("(10 * 5) - 8 / 2") == 46.0
    assert safe_eval_math("2 ** 3") == 8.0

    # Prevent unsafe python code injection
    with pytest.raises((ValueError, SyntaxError, TypeError)):
        safe_eval_math("__import__('os').system('ls')")

    with pytest.raises((ValueError, SyntaxError, TypeError)):
        safe_eval_math("open('/etc/passwd').read()")


def test_safe_tool_harness_execution() -> None:
    harness = SafeToolHarness()

    # Calculator
    res_calc = harness.execute("calculator", {"expression": "100 / 4"})
    assert res_calc.success is True
    assert res_calc.output == {"result": 25.0}
    assert res_calc.policy_violation is False

    # String Reverser
    res_rev = harness.execute("string_reverser", {"text": "EvalForge"})
    assert res_rev.success is True
    assert res_rev.output == {"reversed": "egroFlavE"}

    # Unallowed tool rejected by policy
    res_unallowed = harness.execute(
        "calculator", {"expression": "5 + 5"}, allowed_tools={"weather_lookup"}
    )
    assert res_unallowed.success is False
    assert res_unallowed.policy_violation is True
    assert "Policy violation" in res_unallowed.error


def test_compute_agent_metrics() -> None:
    traces = [
        AgentStepTrace(
            step_number=1,
            tool_name="calculator",
            tool_args={"expression": "5+5"},
            tool_result={"result": 10},
            duration_ms=15.0,
            is_valid_call=True,
        ),
        AgentStepTrace(
            step_number=2,
            tool_name=None,
            thought="The total is 10.",
            duration_ms=20.0,
            is_valid_call=True,
        ),
    ]

    scorecard = compute_agent_metrics(
        traces=traces,
        expected_tools=["calculator"],
        expected_outcome="10",
        final_output="The total is 10.",
        policy_violations=0,
        raw_task_completed=True,
    )

    assert scorecard.tool_accuracy == 1.0
    assert scorecard.schema_validity == 1.0
    assert scorecard.policy_violations == 0
    assert scorecard.task_completed is True
    assert scorecard.total_steps == 2


def test_agent_api_lifecycle() -> None:
    unique_suffix = uuid.uuid4().hex[:8]
    with TestClient(app) as client:
        payload = {
            "name": f"Agent Math Run {unique_suffix}",
            "model_id": "mock-llama-3.1-8b",
            "provider": "mock",
            "task": "Please use tool calculator to evaluate expression 25 * 4.",
            "tools": [
                {
                    "name": "calculator",
                    "description": "Computes arithmetic expression",
                    "parameters": {
                        "type": "object",
                        "properties": {"expression": {"type": "string"}},
                    },
                }
            ],
            "expected_tools": ["calculator"],
            "max_steps": 4,
            "timeout_seconds": 10.0,
        }

        res = client.post("/api/v1/agent-evaluations", json=payload)
        assert res.status_code == 201
        eval_data = res.json()
        eval_id = eval_data["id"]

        assert eval_data["model_id"] == "mock-llama-3.1-8b"
        assert eval_data["status"] == "completed"
        assert eval_data["total_steps"] >= 1
        assert eval_data["policy_violations"] == 0

        # Retrieve evaluation summary
        get_res = client.get(f"/api/v1/agent-evaluations/{eval_id}")
        assert get_res.status_code == 200
        assert get_res.json()["id"] == eval_id

        # Retrieve traces
        trace_res = client.get(f"/api/v1/agent-evaluations/{eval_id}/traces")
        assert trace_res.status_code == 200
        traces = trace_res.json()
        assert len(traces) >= 1
        assert traces[0]["step_number"] == 1
