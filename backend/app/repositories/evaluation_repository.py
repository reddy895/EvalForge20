"""Data access repository for evaluation runs and case results."""

from datetime import datetime, timezone

from backend.app.models.entities import CaseResultORM, EvaluationRunORM
from backend.app.schemas.evaluations import (
    AggregateMetrics,
    CaseMetricResult,
    CaseResult,
    EvaluationRunDetail,
    EvaluationRunSummary,
)
from sqlalchemy.orm import Session


class EvaluationRepository:
    """Manages persistence of evaluation runs and individual test case results."""

    def __init__(self, db: Session):
        self.db = db

    def create_run(
        self,
        run_id: str,
        name: str,
        model_identifier: str,
        provider: str,
        task_id: str,
        total_cases: int,
    ) -> EvaluationRunORM:
        run = EvaluationRunORM(
            id=run_id,
            name=name,
            model_identifier=model_identifier,
            provider=provider,
            task_id=task_id,
            status="running",
            total_cases=total_cases,
            completed_cases=0,
            failed_cases=0,
            created_at=datetime.now(timezone.utc),
        )
        self.db.add(run)
        self.db.commit()
        self.db.refresh(run)
        return run

    def record_case_result(
        self,
        run_id: str,
        case_id: str,
        prompt: str,
        expected_output: str | None,
        actual_output: str | None,
        passed: bool,
        latency_ms: float,
        error_message: str | None = None,
        error_category: str | None = None,
        metrics: list[dict] | None = None,
    ) -> CaseResultORM:
        case = CaseResultORM(
            run_id=run_id,
            case_id=case_id,
            prompt=prompt,
            expected_output=expected_output,
            actual_output=actual_output,
            passed=passed,
            latency_ms=latency_ms,
            error_message=error_message,
            error_category=error_category,
            metrics_json=metrics or [],
        )
        self.db.add(case)
        self.db.commit()
        self.db.refresh(case)
        return case

    def complete_run(
        self,
        run_id: str,
        status: str,
        completed_cases: int,
        failed_cases: int,
        pass_rate: float | None,
        mean_latency_ms: float | None,
        aggregates: dict,
    ) -> EvaluationRunORM | None:
        run = self.db.query(EvaluationRunORM).filter(EvaluationRunORM.id == run_id).first()
        if not run:
            return None
        run.status = status
        run.completed_cases = completed_cases
        run.failed_cases = failed_cases
        run.pass_rate = pass_rate
        run.mean_latency_ms = mean_latency_ms
        run.aggregates_json = aggregates
        run.completed_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(run)
        return run

    def list_runs(self, limit: int = 50, offset: int = 0) -> list[EvaluationRunSummary]:
        records = (
            self.db.query(EvaluationRunORM)
            .order_by(EvaluationRunORM.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )
        return [
            EvaluationRunSummary(
                id=r.id,
                name=r.name,
                model_identifier=r.model_identifier,
                provider=r.provider,
                task_id=r.task_id,
                status=r.status,
                total_cases=r.total_cases,
                completed_cases=r.completed_cases,
                pass_rate=r.pass_rate,
                mean_latency_ms=r.mean_latency_ms,
                created_at=r.created_at,
                completed_at=r.completed_at,
            )
            for r in records
        ]

    def get_run_detail(self, run_id: str) -> EvaluationRunDetail | None:
        run = self.db.query(EvaluationRunORM).filter(EvaluationRunORM.id == run_id).first()
        if not run:
            return None

        cases = (
            self.db.query(CaseResultORM)
            .filter(CaseResultORM.run_id == run_id)
            .order_by(CaseResultORM.id.asc())
            .all()
        )

        case_results = []
        for c in cases:
            m_list = []
            for m in c.metrics_json or []:
                m_list.append(
                    CaseMetricResult(
                        metric_name=m.get("metric_name", "unknown"),
                        passed=m.get("passed", False),
                        score=float(m.get("score", 0.0)),
                        details=m.get("details"),
                    )
                )
            case_results.append(
                CaseResult(
                    case_id=c.case_id,
                    prompt=c.prompt,
                    expected_output=c.expected_output,
                    actual_output=c.actual_output,
                    passed=c.passed,
                    latency_ms=c.latency_ms,
                    error_message=c.error_message,
                    error_category=c.error_category,
                    metrics=m_list,
                )
            )

        raw_agg = run.aggregates_json or {}
        aggregates = AggregateMetrics(
            total_cases=run.total_cases,
            completed_cases=run.completed_cases,
            failed_cases=run.failed_cases,
            pass_rate=run.pass_rate,
            mean_latency_ms=run.mean_latency_ms,
            p95_latency_ms=raw_agg.get("p95_latency_ms"),
            total_tokens=raw_agg.get("total_tokens"),
            metric_averages=raw_agg.get("metric_averages", {}),
            error_distribution=raw_agg.get("error_distribution", {}),
        )

        return EvaluationRunDetail(
            id=run.id,
            name=run.name,
            model_identifier=run.model_identifier,
            provider=run.provider,
            task_id=run.task_id,
            status=run.status,
            total_cases=run.total_cases,
            completed_cases=run.completed_cases,
            pass_rate=run.pass_rate,
            aggregates=aggregates,
            case_results=case_results,
            created_at=run.created_at,
            completed_at=run.completed_at,
        )
