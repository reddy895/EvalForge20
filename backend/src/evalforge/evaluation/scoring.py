"""Evaluation scoring coordinator and metric aggregator."""

from typing import Any

class EvaluationScorer:
    """Coordinates deterministic metric evaluations on actual vs expected model outputs."""

    @staticmethod
    def score_exact_match(actual: str, expected: str, case_sensitive: bool = False) -> bool:
        if case_sensitive:
            return actual.strip() == expected.strip()
        return actual.strip().lower() == expected.strip().lower()

    @staticmethod
    def score_contains(actual: str, expected_keyword: str) -> bool:
        return expected_keyword.strip().lower() in actual.strip().lower()

    @staticmethod
    def compute_summary_score(case_results: list[dict[str, Any]]) -> dict[str, float]:
        if not case_results:
            return {"pass_rate": 0.0, "total_cases": 0}
        total = len(case_results)
        passed = sum(1 for c in case_results if c.get("passed", False))
        return {
            "pass_rate": round((passed / total) * 100.0, 1),
            "total_cases": total,
            "passed_cases": passed,
            "failed_cases": total - passed,
        }
