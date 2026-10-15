"""Composite evaluator combining multiple weighted component metrics with transparent scoring."""

from app.domain.contracts import EvaluatorContract, EvaluatorInput
from app.domain.errors import EvaluatorError
from app.domain.results import MetricResult
from app.evaluators.registry import MetricCategory, MetricDefinition, registry


class CompositeEvaluator(EvaluatorContract):
    """Evaluates multiple component metrics, computing an explicitly weighted score without hiding component failures."""

    @property
    def metric_id(self) -> str:
        return "composite_score"

    @property
    def metric_name(self) -> str:
        return "Composite Quality Score"

    async def evaluate(self, eval_input: EvaluatorInput) -> MetricResult:
        opts = eval_input.options
        weights: dict[str, float] = opts.get("weights", {"exact_match": 0.5, "json_validity": 0.5})
        threshold: float = opts.get("threshold", 0.7)
        require_all: bool = opts.get("require_all", True)

        # Validate weights configuration
        if not weights or any(w < 0 for w in weights.values()):
            raise EvaluatorError(
                "Composite weights must be a non-empty mapping of non-negative floats",
                metric_id=self.metric_id,
            )

        total_weight = sum(weights.values())
        if total_weight <= 0:
            raise EvaluatorError(
                "Sum of composite weights must be greater than zero", metric_id=self.metric_id
            )

        component_scores: dict[str, float | None] = {}
        component_passed: dict[str, bool | None] = {}
        weighted_sum = 0.0
        active_weight = 0.0
        missing_components: list[str] = []

        for m_id, weight in weights.items():
            try:
                evaluator = registry.get(m_id)
                res = await evaluator.evaluate(eval_input)
                component_scores[m_id] = res.score
                component_passed[m_id] = res.passed

                if res.score is not None:
                    weighted_sum += weight * res.score
                    active_weight += weight
                else:
                    missing_components.append(m_id)
            except Exception:
                component_scores[m_id] = None
                component_passed[m_id] = False
                missing_components.append(m_id)

        if require_all and missing_components:
            return MetricResult(
                metric_id=self.metric_id,
                metric_name=self.metric_name,
                score=None,
                passed=False,
                reason=f"Composite evaluation missing required component metrics: {missing_components}",
                details={
                    "component_scores": component_scores,
                    "component_passed": component_passed,
                    "missing_components": missing_components,
                },
                is_model_based=False,
            )

        final_score = round(weighted_sum / active_weight, 4) if active_weight > 0 else 0.0
        # Passing requires score >= threshold AND no hard component failures
        has_failed_component = any(p is False for p in component_passed.values())
        passed = (final_score >= threshold) and not has_failed_component

        return MetricResult(
            metric_id=self.metric_id,
            metric_name=self.metric_name,
            score=final_score,
            passed=passed,
            reason=(
                f"Composite score {final_score:.2f} >= threshold {threshold:.2f}"
                if passed
                else f"Composite score {final_score:.2f} failed quality criteria (failed components: {[k for k, v in component_passed.items() if v is False]})"
            ),
            details={
                "component_scores": component_scores,
                "component_passed": component_passed,
                "weights": weights,
                "threshold": threshold,
            },
            is_model_based=False,
        )


registry.register(
    CompositeEvaluator,
    MetricDefinition(
        metric_id="composite_score",
        metric_name="Composite Quality Score",
        description="Combines multiple weighted component metrics with explicit weights and retained component scores.",
        category=MetricCategory.COMPOSITE,
        requires_expected_output=False,
    ),
)
