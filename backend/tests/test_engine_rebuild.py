"""Tests for visual workflow validation, engine registry, and execution scheduler."""

import asyncio
import pytest

from src.evalforge.engine.events import ExecutionEventBroadcaster
from src.evalforge.engine.registry import EngineRegistry
from src.evalforge.engine.scheduler import WorkflowScheduler
from src.evalforge.engine.validator import WorkflowValidator
from src.evalforge.schemas.main import WorkflowEdge, WorkflowGraph, WorkflowNode


def test_workflow_validator_valid_pipeline():
    graph = WorkflowGraph(
        nodes=[
            WorkflowNode(id="n_ds", type="dataset", name="My Dataset", category="dataset", data={"cases": [{"input": "hi", "expected_output": "hello"}]}),
            WorkflowNode(id="n_mod", type="model", name="qwen2.5:3b", category="model", data={"model_identifier": "qwen2.5:3b"}),
            WorkflowNode(id="n_ev", type="evaluator", name="exact_match", category="evaluator", data={"evaluator_id": "exact_match"}),
        ],
        edges=[
            WorkflowEdge(id="e1", source="n_ds", target="n_mod"),
            WorkflowEdge(id="e2", source="n_mod", target="n_ev"),
        ],
    )
    res = WorkflowValidator.validate_graph(graph)
    assert res.is_valid is True
    assert len(res.errors) == 0
    assert "qwen2.5:3b" in res.executable_models


def test_workflow_validator_missing_model():
    graph = WorkflowGraph(
        nodes=[
            WorkflowNode(id="n_ds", type="dataset", name="Dataset", category="dataset"),
            WorkflowNode(id="n_ev", type="evaluator", name="accuracy", category="evaluator"),
        ],
        edges=[],
    )
    res = WorkflowValidator.validate_graph(graph)
    assert res.is_valid is False
    assert any("at least one Model node" in e.message for e in res.errors)


def test_workflow_validator_cycle_detection():
    graph = WorkflowGraph(
        nodes=[
            WorkflowNode(id="n1", type="dataset", name="Dataset", category="dataset"),
            WorkflowNode(id="n2", type="model", name="Model", category="model"),
            WorkflowNode(id="n3", type="evaluator", name="Evaluator", category="evaluator"),
        ],
        edges=[
            WorkflowEdge(id="e1", source="n1", target="n2"),
            WorkflowEdge(id="e2", source="n2", target="n3"),
            WorkflowEdge(id="e3", source="n3", target="n1"),
        ],
    )
    res = WorkflowValidator.validate_graph(graph)
    assert res.is_valid is False
    assert any("circular" in e.message for e in res.errors)


def test_engine_registry_resolves_evaluators():
    reg = EngineRegistry()
    ev1 = reg.resolve_evaluator("exact_match")
    assert ev1.name == "exact_match"

    ev2 = reg.resolve_evaluator("latency")
    assert ev2.name == "latency"

    ev3 = reg.resolve_evaluator("functional_correctness")
    assert ev3.name == "functional_correctness"


@pytest.mark.asyncio
async def test_workflow_scheduler_concurrency_and_cancellation():
    scheduler = WorkflowScheduler(concurrency_limit=2)
    exec_id = "test-exec-1"
    token = scheduler.register_execution(exec_id)

    assert not scheduler.is_cancelled(exec_id)
    scheduler.cancel_execution(exec_id)
    assert scheduler.is_cancelled(exec_id)
    assert token.is_set()

    # Throttled execution
    async def sample_work():
        await asyncio.sleep(0.01)
        return "done"

    res = await scheduler.run_throttled(sample_work())
    assert res == "done"
    scheduler.unregister_execution(exec_id)


@pytest.mark.asyncio
async def test_event_broadcaster():
    broadcaster = ExecutionEventBroadcaster()
    exec_id = "test-exec-events"

    queue = broadcaster.subscribe(exec_id)
    await broadcaster.broadcast(
        execution_id=exec_id,
        event_type="started",
        message="Workflow started",
        total_steps=10,
    )

    ev = await asyncio.wait_for(queue.get(), timeout=1.0)
    assert ev is not None
    assert ev.event_type == "started"
    assert ev.total_steps == 10
    broadcaster.unsubscribe(exec_id, queue)
