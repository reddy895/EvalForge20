"""Comprehensive end-to-end integration tests for local-first transformation."""

from pathlib import Path

import pytest
from app.application.evaluation_service import EvaluationService
from app.comparisons.comparator import RegressionThresholds, compare_evaluation_runs
from app.comparisons.multi_comparator import compare_multiple_runs
from app.datasets.loader import DatasetLoader
from app.domain.contracts import ProviderResponse
from app.domain.models import EvaluatorConfiguration, TargetConfiguration, TargetType
from app.domain.state import EvaluationRunStatus
from app.providers.ollama import OllamaProvider
from app.reporting.csv_exporter import generate_csv_report
from app.reporting.json_exporter import generate_json_report
from app.reporting.markdown_exporter import generate_markdown_report
from app.runner.config import EvaluationRunConfig
from app.storage.database import get_db


@pytest.mark.asyncio
async def test_end_to_end_local_first_workflow(monkeypatch, tmp_path: Path):
    """Verify complete end-to-end local-first workflow without LangSmith or paid cloud APIs."""
    # 1. Multi-format dataset loading and validation
    fixtures = [
        "examples/datasets/qa_sample.json",
        "examples/datasets/classification_sample.csv",
        "examples/datasets/rag_sample.jsonl",
        "examples/datasets/agent_sample.jsonl",
    ]
    for fix_path in fixtures:
        p = Path(fix_path)
        assert p.exists(), f"Sample fixture '{fix_path}' must exist"
        report = DatasetLoader.load(p)
        assert report.is_valid is True, f"Fixture '{fix_path}' validation failed: {report.issues}"
        assert len(report.cases) > 0

    # 2. Mock Ollama generation for local evaluation
    async def mock_ollama_generate(self, req):
        prompt_text = req.prompt.lower()
        if "japan" in prompt_text:
            text = "Tokyo"
        elif "relativity" in prompt_text:
            text = "Albert Einstein"
        elif "ocean" in prompt_text:
            text = "Pacific Ocean"
        else:
            text = "Sample response"

        return ProviderResponse(
            output_text=text,
            latency_ms=85.0,
            token_usage={"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
            is_success=True,
        )

    monkeypatch.setattr(OllamaProvider, "generate", mock_ollama_generate)

    # 3. Execute Run 1 (Model: qwen2.5:3b)
    db = next(get_db())
    service = EvaluationService(db)

    qa_report = DatasetLoader.load("examples/datasets/qa_sample.json")
    config_qwen = EvaluationRunConfig(
        name="Qwen 2.5 3B Benchmark",
        dataset_cases=qa_report.cases,
        target=TargetConfiguration(
            target_name="Ollama Qwen",
            target_type=TargetType.OLLAMA,
            provider_name="ollama",
            model_identifier="qwen2.5:3b",
        ),
        evaluators=[
            EvaluatorConfiguration(evaluator_name="exact_match", metric_id="exact_match"),
            EvaluatorConfiguration(evaluator_name="token_f1", metric_id="token_f1"),
            EvaluatorConfiguration(
                evaluator_name="response_completeness",
                metric_id="response_completeness",
                options={"min_words": 1},
            ),
        ],
    )

    run_qwen, cases_qwen, aggs_qwen = await service.run_evaluation(config_qwen)
    assert run_qwen.status == EvaluationRunStatus.COMPLETED
    assert run_qwen.completed_cases == 3
    assert run_qwen.failed_cases == 0

    assert aggs_qwen is not None
    assert aggs_qwen.pass_rate is not None
    assert aggs_qwen.pass_rate >= 0.66
    assert len(cases_qwen) == 3

    # 4. Execute Run 2 (Model: llama3.2:1b)
    config_llama = EvaluationRunConfig(
        name="Llama 3.2 1B Benchmark",
        dataset_cases=qa_report.cases,
        target=TargetConfiguration(
            target_name="Ollama Llama",
            target_type=TargetType.OLLAMA,
            provider_name="ollama",
            model_identifier="llama3.2:1b",
        ),
        evaluators=[
            EvaluatorConfiguration(evaluator_name="exact_match", metric_id="exact_match"),
            EvaluatorConfiguration(evaluator_name="token_f1", metric_id="token_f1"),
        ],
    )

    run_llama, cases_llama, aggs_llama = await service.run_evaluation(config_llama)
    assert run_llama.status == EvaluationRunStatus.COMPLETED
    assert aggs_llama is not None

    # 5. Pairwise Run Comparison
    comparison = compare_evaluation_runs(
        baseline=run_qwen,
        baseline_cases=cases_qwen,
        baseline_aggs=aggs_qwen,
        candidate=run_llama,
        candidate_cases=cases_llama,
        candidate_aggs=aggs_llama,
        thresholds=RegressionThresholds(max_allowed_pass_rate_drop=0.5),
        allow_different_datasets=True,
    )
    assert comparison.is_compatible is True
    assert "exact_match" in comparison.metric_deltas

    # 6. Multi-Run Comparison Matrix
    matrix = compare_multiple_runs(
        runs=[run_qwen, run_llama],
        cases_by_run={run_qwen.run_id: cases_qwen, run_llama.run_id: cases_llama},
    )
    assert len(matrix.runs) == 2
    assert matrix.fastest_run_id is not None
    assert matrix.highest_accuracy_run_id is not None
    assert "Compared 2 evaluation runs" in matrix.summary

    # 7. Generate Multi-format Reports
    # JSON report
    json_rep = generate_json_report(run_qwen, cases_qwen, aggs_qwen)
    assert json_rep["run_id"] == run_qwen.run_id
    assert json_rep["case_counts"]["completed_cases"] == 3

    # Markdown report
    md_rep = generate_markdown_report(run_qwen, cases_qwen, aggs_qwen)
    assert f"# Evaluation Report: {run_qwen.name}" in md_rep
    assert "**Target Model:** `qwen2.5:3b`" in md_rep
    assert "Zero cloud API fees incurred" in md_rep

    # CSV report
    csv_rep = generate_csv_report(run_qwen, cases_qwen)
    assert "case_id,run_id,model_identifier,input" in csv_rep
    assert "qwen2.5:3b" in csv_rep
    assert "exact_match_score" in csv_rep

    # 8. Query History and Run Filtering
    all_runs = service.list_runs()
    assert len(all_runs) >= 2

    qwen_filtered = service.list_runs(model_identifier="qwen2.5:3b")
    assert any(r.run_id == run_qwen.run_id for r in qwen_filtered)

    status_filtered = service.list_runs(status=EvaluationRunStatus.COMPLETED)
    assert len(status_filtered) >= 2
