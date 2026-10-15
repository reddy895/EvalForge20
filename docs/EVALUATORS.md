# EvalForge20 Evaluators Guide

## 1. Evaluator Contract

All evaluators implement the asynchronous `EvaluatorContract`:

```python
class EvaluatorContract(ABC):
    @property
    @abstractmethod
    def metric_id(self) -> str:
        ...

    @property
    @abstractmethod
    def metric_name(self) -> str:
        ...

    @abstractmethod
    async def evaluate(self, eval_input: EvaluatorInput) -> MetricResult:
        ...
```

### EvaluatorInput
Contains:
- `case`: Complete `EvaluationCase` instance with input, expected_output, tags, category, and metadata.
- `actual_output`: Model response string or serialized agent trace.
- `options`: Metric-specific options (e.g. weights, schemas, thresholds, k).

### MetricResult
Returns:
- `metric_id`: Unique identifier.
- `score`: Optional float (typically 0.0 to 1.0). `None` if skipped.
- `passed`: Optional boolean pass/fail status.
- `reason`: Human-readable explanation.
- `details`: Structured payload (e.g. hits, component scores, violations).
- `is_model_based`: Explicit flag indicating whether an LLM was used as a judge.

## 2. Central Evaluator Registry

EvalForge20 uses a thread-safe registry singleton (`app.evaluators.registry`):

```python
from app.evaluators.registry import registry

# Check registration
if registry.is_registered("exact_match"):
    evaluator = registry.get("exact_match")

# List all metrics
for defn in registry.list_metrics():
    print(defn.metric_id, defn.category, defn.description)
```

## 3. Composite Evaluators

The `composite_score` evaluator combines multiple component metrics:
- Weights are explicitly defined (e.g. `{"exact_match": 0.6, "json_validity": 0.4}`).
- Negative weights are rejected.
- Component scores and pass/fail states are preserved in `result.details`.
- Hard failures are propagated: if any required component fails, the composite result will not pass regardless of average score.
