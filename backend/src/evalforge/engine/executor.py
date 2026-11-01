"""End-to-end visual workflow execution engine with fair benchmarking guarantees."""

import asyncio
import time
import uuid
from typing import Any

from src.evalforge.database.models import CaseResultRecord, ExecutionRecord
from src.evalforge.database.session import get_db_context
from src.evalforge.engine.events import get_event_broadcaster
from src.evalforge.engine.registry import EngineRegistry, ModelExecutionTarget
from src.evalforge.engine.scheduler import get_workflow_scheduler
from src.evalforge.engine.validator import WorkflowValidator
from src.evalforge.evaluators.base import MetricResult
from src.evalforge.experiments.repository import ExperimentRepository
from src.evalforge.hardware.monitor import get_hardware_monitor
from src.evalforge.providers.base import BaseProvider
from src.evalforge.providers.registry import get_provider_registry
from src.evalforge.providers.schemas import InferenceRequest, InferenceResponse
from src.evalforge.schemas.main import WorkflowGraph


class WorkflowExecutor:
    """Executes validated visual node workflows, performing inference and metric calculation."""

    def __init__(self) -> None:
        self.validator = WorkflowValidator()
        self.registry = EngineRegistry()
        self.scheduler = get_workflow_scheduler()
        self.broadcaster = get_event_broadcaster()
        self.hardware_monitor = get_hardware_monitor()
        self.provider_registry = get_provider_registry()

    async def execute_workflow(
        self,
        graph: WorkflowGraph,
        execution_id: str | None = None,
        workflow_id: str | None = None,
        name: str | None = None,
        judge_model_identifier: str | None = None,
    ) -> dict[str, Any]:
        exec_id = execution_id or str(uuid.uuid4())
        workflow_name = name or "Evaluation Workflow"

        # 1. Validate graph structure
        val_result = self.validator.validate_graph(graph)
        if not val_result.is_valid:
            err_msg = "; ".join(e.message for e in val_result.errors)
            await self.broadcaster.broadcast(
                execution_id=exec_id,
                event_type="failed",
                message=f"Validation failed: {err_msg}",
            )
            return {
                "execution_id": exec_id,
                "status": "FAILED",
                "error": err_msg,
                "validation": val_result.model_dump(),
            }

        # 2. Register cancellation token and initial DB state
        cancel_token = self.scheduler.register_execution(exec_id)
        hw_before = self.hardware_monitor.capture_snapshot()

        targets = self.registry.build_execution_targets(graph, judge_model=judge_model_identifier)
        total_steps = sum(len(t.dataset_records) for t in targets)
        completed_steps = 0

        await self.broadcaster.broadcast(
            execution_id=exec_id,
            event_type="started",
            message=f"Started execution '{workflow_name}' across {len(targets)} models ({total_steps} total cases).",
            total_steps=total_steps,
            completed_steps=0,
            progress_percentage=0.0,
        )

        experiment_records = []

        try:
            # 3. Fair Benchmarking Execution Loop
            for target in targets:
                if cancel_token.is_set():
                    break

                model_id = target.model_identifier
                provider = self.provider_registry.resolve_model_provider(model_id)

                case_results: list[dict[str, Any]] = []
                metric_scores: dict[str, list[float]] = {}

                for idx, record in enumerate(target.dataset_records, start=1):
                    if cancel_token.is_set():
                        break

                    case_start = time.perf_counter()
                    req = InferenceRequest(
                        model=model_id,
                        prompt=record.input,
                        temperature=0.0,
                    )

                    resp: InferenceResponse | None = None
                    exec_err: str | None = None
                    is_timeout = False

                    try:
                        # Throttled inference execution
                        resp = await self.scheduler.run_throttled(
                            provider.generate(req),
                            timeout=60.0,
                        )
                        prediction = resp.text if resp else ""
                        latency_ms = resp.latency_ms if resp and resp.latency_ms else (time.perf_counter() - case_start) * 1000.0
                    except TimeoutError:
                        is_timeout = True
                        exec_err = "Inference timed out after 60s"
                        prediction = ""
                        latency_ms = 60000.0
                    except Exception as exc:
                        exec_err = str(exc)
                        prediction = ""
                        latency_ms = (time.perf_counter() - case_start) * 1000.0

                    # Run selected evaluators
                    eval_results: dict[str, MetricResult] = {}
                    overall_passed = not exec_err and not is_timeout

                    for evaluator in target.evaluators:
                        res = await evaluator.evaluate(
                            prediction=prediction,
                            reference=record.expected_output,
                            context=record.context,
                            latency_ms=latency_ms,
                            is_timeout=is_timeout,
                            error_message=exec_err,
                        )
                        eval_results[evaluator.name] = res
                        metric_scores.setdefault(evaluator.name, []).append(res.score)
                        if not res.passed:
                            overall_passed = False

                    completed_steps += 1
                    pct = (completed_steps / total_steps) * 100.0 if total_steps > 0 else 100.0

                    case_data = {
                        "case_index": idx,
                        "prompt": record.input,
                        "expected_output": record.expected_output,
                        "actual_output": prediction,
                        "passed": overall_passed,
                        "latency_ms": round(latency_ms, 2),
                        "evaluators": {k: v.model_dump() for k, v in eval_results.items()},
                        "error_message": exec_err,
                    }
                    case_results.append(case_data)

                    await self.broadcaster.broadcast(
                        execution_id=exec_id,
                        event_type="step_progress",
                        message=f"[{model_id}] Case {idx}/{len(target.dataset_records)} evaluated (latency: {latency_ms:.1f}ms).",
                        total_steps=total_steps,
                        completed_steps=completed_steps,
                        progress_percentage=pct,
                        data={
                            "model": model_id,
                            "case": case_data,
                        },
                    )

                # Compute aggregate metrics for this model target
                aggregated_metrics: dict[str, Any] = {
                    "total_cases": len(case_results),
                    "passed_cases": sum(1 for c in case_results if c["passed"]),
                    "pass_rate": round(sum(1 for c in case_results if c["passed"]) / len(case_results), 4) if case_results else 0.0,
                    "avg_latency_ms": round(sum(c["latency_ms"] for c in case_results) / len(case_results), 2) if case_results else 0.0,
                }
                for m_name, scores in metric_scores.items():
                    if scores:
                        aggregated_metrics[m_name] = round(sum(scores) / len(scores), 4)

                hw_after = self.hardware_monitor.capture_snapshot()

                # Persist Experiment
                exp_record = await ExperimentRepository.create(
                    name=f"{workflow_name} - {model_id}",
                    model_identifier=model_id,
                    workflow_id=workflow_id,
                    execution_id=exec_id,
                    evaluator_ids=[e.name for e in target.evaluators],
                    metrics=aggregated_metrics,
                    parameters={"cases": case_results},
                    hardware={"before": hw_before, "after": hw_after},
                    status="COMPLETED" if not cancel_token.is_set() else "CANCELLED",
                )
                experiment_records.append(exp_record)

            final_status = "CANCELLED" if cancel_token.is_set() else "COMPLETED"
            await self.broadcaster.broadcast(
                execution_id=exec_id,
                event_type="completed" if final_status == "COMPLETED" else "cancelled",
                message=f"Workflow execution {final_status.lower()}.",
                total_steps=total_steps,
                completed_steps=completed_steps,
                progress_percentage=100.0,
                data={"experiments_count": len(experiment_records)},
            )

            return {
                "execution_id": exec_id,
                "status": final_status,
                "experiments": [e.id for e in experiment_records],
                "total_steps": total_steps,
                "completed_steps": completed_steps,
            }
        finally:
            self.scheduler.unregister_execution(exec_id)


_global_executor: WorkflowExecutor | None = None


def get_workflow_executor() -> WorkflowExecutor:
    global _global_executor
    if _global_executor is None:
        _global_executor = WorkflowExecutor()
    return _global_executor


__all__ = [
    "WorkflowExecutor",
    "get_workflow_executor",
]
