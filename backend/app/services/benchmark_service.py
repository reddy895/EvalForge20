"""Benchmark execution engine running test cases against local or mock models."""

import json
import statistics
import time
from pathlib import Path
from typing import Any

from backend.app.core.errors import ErrorCode, EvalForgeError
from backend.app.core.logging import get_logger
from backend.app.evaluators.deterministic import (
    JsonValidityEvaluator,
    KeywordContainsEvaluator,
    NormalizedMatchEvaluator,
)
from backend.app.repositories.evaluation_repository import EvaluationRepository
from backend.app.schemas.evaluations import (
    EvaluationCase,
    EvaluationRunCreate,
    EvaluationRunDetail,
)
from backend.app.services.ollama_service import OllamaService
from sqlalchemy.orm import Session

logger = get_logger("benchmark_service")
BENCHMARK_DIR = Path(__file__).resolve().parent.parent.parent.parent / "benchmarks" / "datasets"


class BenchmarkService:
    """Loads benchmark test suites and coordinates live model evaluation."""

    def __init__(self, db: Session, ollama_service: OllamaService | None = None):
        self.db = db
        self.repo = EvaluationRepository(db)
        self.ollama = ollama_service or OllamaService()

    def list_available_tasks(self) -> list[dict[str, Any]]:
        """List registered benchmark datasets with metadata and case counts."""
        tasks = []
        if not BENCHMARK_DIR.exists():
            return tasks

        for file_path in BENCHMARK_DIR.glob("*.json"):
            try:
                with open(file_path, encoding="utf-8") as f:
                    data = json.load(f)
                    tasks.append(
                        {
                            "task_id": data.get("task_id", file_path.stem),
                            "name": data.get("name", file_path.stem.replace("_", " ").title()),
                            "description": data.get("description", ""),
                            "total_cases": len(data.get("cases", [])),
                        }
                    )
            except Exception as e:
                logger.warning(f"Error loading benchmark file {file_path}: {e}")
        return tasks

    def load_task_cases(self, task_id: str) -> list[EvaluationCase]:
        """Load test cases for a specific benchmark task."""
        file_path = BENCHMARK_DIR / f"{task_id}.json"
        if not file_path.exists():
            # Fallback to finding by task_id in any file
            for candidate in BENCHMARK_DIR.glob("*.json"):
                try:
                    with open(candidate, encoding="utf-8") as f:
                        data = json.load(f)
                        if data.get("task_id") == task_id:
                            file_path = candidate
                            break
                except Exception:
                    pass

        if not file_path.exists():
            raise EvalForgeError(f"Benchmark task '{task_id}' not found.", ErrorCode.NOT_FOUND)

        with open(file_path, encoding="utf-8") as f:
            data = json.load(f)
            cases = []
            for c in data.get("cases", []):
                cases.append(
                    EvaluationCase(
                        id=c["id"],
                        prompt=c["prompt"],
                        expected_output=c.get("expected_output"),
                        task_category=data.get("task_id", "general"),
                        assertions=c.get("assertions", []),
                    )
                )
            return cases

    async def run_evaluation(self, req: EvaluationRunCreate) -> EvaluationRunDetail:
        """Execute evaluation run across the requested benchmark cases."""
        cases = self.load_task_cases(req.task_id)[: req.max_cases]
        if not cases:
            raise EvalForgeError(
                "No test cases available for evaluation.", ErrorCode.VALIDATION_ERROR
            )

        run_id = f"run_{int(time.time() * 1000)}"
        self.repo.create_run(
            run_id=run_id,
            name=req.name,
            model_identifier=req.model_identifier,
            provider=req.provider,
            task_id=req.task_id,
            total_cases=len(cases),
        )

        latencies = []
        passed_flags = []
        completed_cases = 0
        failed_cases = 0
        error_distribution: dict[str, int] = {}

        for case in cases:
            start_case = time.perf_counter()
            actual_text = None
            err_msg = None
            err_cat = None
            case_passed = False
            case_metrics = []

            try:
                # 1. Model inference execution
                if req.provider == "mock" or req.model_identifier == "mock-model-v1":
                    # Instant deterministic mock
                    await self._simulate_mock_delay()
                    actual_text = case.expected_output or "Mock successful model response."
                    latency_ms = 4.5
                else:
                    # Real Ollama inference
                    result = await self.ollama.generate(
                        model=req.model_identifier,
                        prompt=case.prompt,
                        temperature=req.temperature,
                    )
                    actual_text = result["output"]
                    latency_ms = result["latency_ms"]

                latencies.append(latency_ms)

                # 2. Apply evaluators
                # Evaluator A: Keyword/assertions
                if case.assertions:
                    m_kw = KeywordContainsEvaluator.evaluate(actual_text, case.assertions)
                    case_metrics.append(m_kw.model_dump())
                    case_passed = m_kw.passed
                else:
                    m_norm = NormalizedMatchEvaluator.evaluate(actual_text, case.expected_output)
                    case_metrics.append(m_norm.model_dump())
                    case_passed = m_norm.passed

                # Evaluator B: JSON parsing if structured task
                if req.task_id == "structured_json" or "json" in req.task_id:
                    m_json, _ = JsonValidityEvaluator.evaluate(actual_text)
                    case_metrics.append(m_json.model_dump())
                    case_passed = case_passed and m_json.passed

                passed_flags.append(case_passed)
                completed_cases += 1

            except EvalForgeError as e:
                latency_ms = round((time.perf_counter() - start_case) * 1000.0, 2)
                err_msg = e.message
                err_cat = e.code.value
                failed_cases += 1
                error_distribution[err_cat] = error_distribution.get(err_cat, 0) + 1
            except Exception as e:
                latency_ms = round((time.perf_counter() - start_case) * 1000.0, 2)
                err_msg = str(e)
                err_cat = "execution_error"
                failed_cases += 1
                error_distribution[err_cat] = error_distribution.get(err_cat, 0) + 1

            # Save per-case result
            self.repo.record_case_result(
                run_id=run_id,
                case_id=case.id,
                prompt=case.prompt,
                expected_output=case.expected_output,
                actual_output=actual_text,
                passed=case_passed,
                latency_ms=latency_ms,
                error_message=err_msg,
                error_category=err_cat,
                metrics=case_metrics,
            )

        # 3. Finalize aggregates and run record
        pass_rate = (
            round(sum(1 for p in passed_flags if p) / len(passed_flags), 4)
            if passed_flags
            else None
        )
        mean_latency = round(statistics.fmean(latencies), 2) if latencies else None

        final_status = "completed"
        if failed_cases > 0 and completed_cases == 0:
            final_status = "failed"
        elif failed_cases > 0:
            final_status = "completed_with_errors"

        aggregates = {
            "p95_latency_ms": round(max(latencies), 2) if latencies else None,
            "error_distribution": error_distribution,
        }

        self.repo.complete_run(
            run_id=run_id,
            status=final_status,
            completed_cases=completed_cases,
            failed_cases=failed_cases,
            pass_rate=pass_rate,
            mean_latency_ms=mean_latency,
            aggregates=aggregates,
        )

        detail = self.repo.get_run_detail(run_id)
        if not detail:
            raise EvalForgeError(
                "Failed to fetch generated run details.", ErrorCode.EVALUATION_ERROR
            )
        return detail

    async def _simulate_mock_delay(self) -> None:
        """Brief deterministic delay for simulated mock inference."""
        pass
