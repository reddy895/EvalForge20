"""Unit tests for deterministic evaluation metrics: Token F1, JSON schema validity, and SLA."""

from src.evalforge.evaluation.metrics_token import compute_token_f1
from src.evalforge.evaluation.metrics_json import validate_json_validity
from src.evalforge.evaluation.metrics_sla import evaluate_sla_latency
from src.evalforge.evaluation.scoring import EvaluationScorer

def test_token_f1_exact() -> None:
    res = compute_token_f1("The quick brown fox", "the quick brown fox")
    assert res.f1 == 1.0
    assert res.precision == 1.0
    assert res.recall == 1.0

def test_token_f1_partial() -> None:
    res = compute_token_f1("Paris is the capital of France", "Capital of France is Paris")
    assert res.f1 > 0.8

def test_json_validity() -> None:
    valid, parsed, err = validate_json_validity('```json\n{"status": "ok", "code": 200}\n```')
    assert valid is True
    assert parsed["status"] == "ok"
    assert err is None

    invalid, _, err_msg = validate_json_validity('{bad json')
    assert invalid is False
    assert err_msg is not None

def test_sla_latency() -> None:
    assert evaluate_sla_latency(150.0, 500.0) is True
    assert evaluate_sla_latency(600.0, 500.0) is False

def test_evaluation_scorer_summary() -> None:
    cases = [{"passed": True}, {"passed": False}, {"passed": True}]
    summary = EvaluationScorer.compute_summary_score(cases)
    assert summary["pass_rate"] == 66.7
    assert summary["total_cases"] == 3
