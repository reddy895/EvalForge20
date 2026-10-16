"""Data access repositories for evaluation runs, results, and datasets."""

import json
from datetime import datetime
from typing import Any

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.domain.models import EvaluatorConfiguration, TargetConfiguration
from app.domain.results import AggregateMetrics, CaseResult, MetricResult
from app.domain.state import EvaluationRunStatus
from app.runner.config import EvaluationRunConfig, EvaluationRunRecord
from app.storage.models import (
    CaseResultModel,
    EvaluationRunModel,
    MetricResultModel,
)


def _dumps(val: Any) -> str:
    return json.dumps(val, ensure_ascii=False)


def _loads(val: str | None) -> Any:
    return json.loads(val) if val else None


class EvaluationRepository:
    """Repository managing persistence and retrieval of evaluation runs and case results."""

    def __init__(self, session: Session):
        self.session = session

    def create_run(self, record: EvaluationRunRecord) -> None:
        """Create initial persistent record for an evaluation run."""
        target_dict = record.config.target.model_dump()
        evaluators_list = [e.model_dump() for e in record.config.evaluators]

        run_model = EvaluationRunModel(
            run_id=record.run_id,
            name=record.name,
            status=record.status.value,
            target_config_json=_dumps(target_dict),
            evaluator_configs_json=_dumps(evaluators_list),
            dataset_version_hash=record.config.dataset_version_hash,
            total_cases=record.total_cases,
            completed_cases=record.completed_cases,
            failed_cases=record.failed_cases,
            started_at=record.started_at,
            completed_at=record.completed_at,
            error_message=record.error_message,
        )
        self.session.add(run_model)
        self.session.commit()

    def update_run_completion(
        self,
        run_id: str,
        status: EvaluationRunStatus,
        aggregates: AggregateMetrics,
        completed_at: datetime,
        error_message: str | None = None,
    ) -> None:
        """Update a run with its final status and aggregate metrics."""
        stmt = select(EvaluationRunModel).where(EvaluationRunModel.run_id == run_id)
        run_model = self.session.scalars(stmt).first()
        if not run_model:
            return

        run_model.status = status.value
        run_model.completed_at = completed_at
        run_model.completed_cases = aggregates.completed_cases
        run_model.failed_cases = aggregates.failed_cases
        run_model.aggregate_metrics_json = _dumps(aggregates.model_dump())
        if error_message:
            run_model.error_message = error_message

        self.session.commit()

    def save_case_result(self, res: CaseResult) -> None:
        """Persist a single case result and its associated metric scores."""
        case_model = CaseResultModel(
            case_id=res.case_id,
            run_id=res.run_id,
            input_json=_dumps(res.input),
            actual_output_json=_dumps(res.actual_output) if res.actual_output is not None else None,
            expected_output_json=_dumps(res.expected_output)
            if res.expected_output is not None
            else None,
            latency_ms=res.latency_ms,
            token_usage_json=_dumps(res.token_usage) if res.token_usage else None,
            error_category=res.error_category,
            error_message=res.error_message,
            trace_json=_dumps(res.trace) if res.trace else None,
        )
        self.session.add(case_model)
        self.session.flush()

        for m in res.metrics:
            m_model = MetricResultModel(
                case_result_id=case_model.id,
                run_id=res.run_id,
                metric_id=m.metric_id,
                metric_name=m.metric_name,
                score=m.score,
                passed=m.passed,
                reason=m.reason,
                details_json=_dumps(m.details),
                is_model_based=m.is_model_based,
            )
            self.session.add(m_model)

        self.session.commit()

    def get_run(self, run_id: str) -> EvaluationRunRecord | None:
        """Retrieve evaluation run record by ID."""
        stmt = select(EvaluationRunModel).where(EvaluationRunModel.run_id == run_id)
        m = self.session.scalars(stmt).first()
        if not m:
            return None

        target_dict = _loads(m.target_config_json)
        evaluators_list = _loads(m.evaluator_configs_json)

        config = EvaluationRunConfig(
            run_id=m.run_id,
            name=m.name,
            dataset_version_hash=m.dataset_version_hash,
            target=TargetConfiguration(**target_dict),
            evaluators=[EvaluatorConfiguration(**e) for e in evaluators_list],
        )

        aggregates = self.get_run_aggregates(m.run_id)
        return EvaluationRunRecord(
            run_id=m.run_id,
            name=m.name,
            status=EvaluationRunStatus(m.status),
            config=config,
            total_cases=m.total_cases,
            completed_cases=m.completed_cases,
            failed_cases=m.failed_cases,
            started_at=m.started_at,
            completed_at=m.completed_at,
            error_message=m.error_message,
            metrics=aggregates,
        )

    def get_run_aggregates(self, run_id: str) -> AggregateMetrics | None:
        """Retrieve aggregate metrics for a run."""
        stmt = select(EvaluationRunModel.aggregate_metrics_json).where(
            EvaluationRunModel.run_id == run_id
        )
        raw = self.session.scalar(stmt)
        if not raw:
            return None
        return AggregateMetrics(**_loads(raw))

    def get_case_results(self, run_id: str) -> list[CaseResult]:
        """Retrieve all case results and their metrics for a given run."""
        stmt = (
            select(CaseResultModel)
            .where(CaseResultModel.run_id == run_id)
            .order_by(CaseResultModel.id)
        )
        case_models = self.session.scalars(stmt).all()

        results: list[CaseResult] = []
        for cm in case_models:
            metrics = [
                MetricResult(
                    metric_id=mm.metric_id,
                    metric_name=mm.metric_name,
                    score=mm.score,
                    passed=mm.passed,
                    reason=mm.reason,
                    details=_loads(mm.details_json) or {},
                    is_model_based=mm.is_model_based,
                )
                for mm in cm.metric_results
            ]
            results.append(
                CaseResult(
                    case_id=cm.case_id,
                    run_id=cm.run_id,
                    input=_loads(cm.input_json),
                    actual_output=_loads(cm.actual_output_json),
                    expected_output=_loads(cm.expected_output_json),
                    metrics=metrics,
                    latency_ms=cm.latency_ms,
                    token_usage=_loads(cm.token_usage_json),
                    error_category=cm.error_category,
                    error_message=cm.error_message,
                    trace=_loads(cm.trace_json),
                )
            )
        return results

    def list_runs(
        self,
        limit: int = 50,
        offset: int = 0,
        status: EvaluationRunStatus | str | None = None,
        model_identifier: str | None = None,
        min_pass_rate: float | None = None,
    ) -> list[EvaluationRunRecord]:
        """List historical evaluation runs with optional status, model, and pass rate filters."""
        stmt = select(EvaluationRunModel).order_by(desc(EvaluationRunModel.started_at))
        if status is not None:
            status_val = status.value if hasattr(status, "value") else str(status)
            stmt = stmt.where(EvaluationRunModel.status == status_val)

        models = self.session.scalars(stmt).all()
        records: list[EvaluationRunRecord] = []
        for m in models:
            rec = self.get_run(m.run_id)
            if not rec:
                continue

            if model_identifier and rec.config.target.model_identifier != model_identifier:
                continue

            if min_pass_rate is not None:
                if not rec.metrics or rec.metrics.pass_rate is None:
                    continue
                if rec.metrics.pass_rate < min_pass_rate:
                    continue

            records.append(rec)

        return records[offset : offset + limit]
