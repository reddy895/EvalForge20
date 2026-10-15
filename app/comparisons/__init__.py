"""Run comparison and regression detection package for EvalForge20."""

from app.comparisons.comparator import (
    CaseRegression,
    ComparisonResult,
    MetricDelta,
    RegressionThresholds,
    calculate_metric_delta,
    compare_evaluation_runs,
    evaluate_regression_thresholds,
    validate_run_compatibility,
)
from app.comparisons.multi_comparator import (
    CaseDisagreement,
    MetricComparisonRow,
    MultiRunComparisonMatrix,
    RunSummaryHeader,
    compare_multiple_runs,
)

__all__ = [
    "CaseDisagreement",
    "CaseRegression",
    "ComparisonResult",
    "MetricComparisonRow",
    "MetricDelta",
    "MultiRunComparisonMatrix",
    "RegressionThresholds",
    "RunSummaryHeader",
    "calculate_metric_delta",
    "compare_evaluation_runs",
    "compare_multiple_runs",
    "evaluate_regression_thresholds",
    "validate_run_compatibility",
]
