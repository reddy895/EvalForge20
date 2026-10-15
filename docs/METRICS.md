# EvalForge20 Metrics Reference

## 1. Metric Categories

Every metric in EvalForge20 is categorized under one of the following classes:
- **Deterministic**: Fast, rule-based, predictable evaluation with zero model cost.
- **Composite**: Weighted combinations of individual metrics with explicit transparency.
- **RAG**: Retrieval precision/recall/MRR and generation groundedness.
- **Agent**: Task completion, tool selection accuracy, tool argument validity, and step efficiency.
- **Summary**: Dataset-wide aggregate statistics with precise denominators.

## 2. Supported Metrics

### Deterministic Metrics
| Metric ID | Name | Requires Reference | Description |
|---|---|---|---|
| `exact_match` | Exact Match | Yes | Binary check (1.0/0.0) if actual matches expected output. |
| `normalized_match` | Normalized Match | Yes | Normalizes whitespace, casing, punctuation, and numeric formats before comparison. |
| `json_validity` | JSON Validity | No | Checks if the output parses as valid JSON object or array. |
| `json_schema` | JSON Schema Validity | No | Validates JSON against a JSON Schema provided in `options["schema"]`. |
| `task_assertions` | Predefined Task Assertions | No | Evaluates safe declarative rules (contains, regex, max_length, disallowed_keywords). |

### Composite Metrics
| Metric ID | Name | Description |
|---|---|---|
| `composite_score` | Composite Quality Score | Explicitly weighted sum across registered component metrics. Preserves individual component scores and fails if hard criteria fail. |

### RAG Metrics
| Metric ID | Name | Description |
|---|---|---|
| `context_precision_at_k` | Context Precision @ K | Fraction of top-K retrieved context documents that are relevant. |
| `context_recall_at_k` | Context Recall @ K | Fraction of all relevant reference documents retrieved in top-K. |
| `hit_rate_at_k` | Hit Rate @ K | Binary check (1.0/0.0) whether at least one relevant document was retrieved. |
| `mrr_at_k` | Reciprocal Rank @ K | Reciprocal rank (1 / rank) of the first relevant document in top-K. |
| `groundedness_overlap` | Groundedness Token Overlap | Overlap ratio of answer terms supported by retrieved context passages. |

### AI Agent Metrics
| Metric ID | Name | Description |
|---|---|---|
| `agent_task_completion` | Agent Task Completion | Verifies whether the agent marked task completed and produced a matching answer. |
| `tool_selection_accuracy` | Tool Selection Accuracy | Trajectory match between invoked tools and reference sequence. |
| `tool_argument_validity` | Tool Argument Validity | Proportion of tool calls satisfying required schema arguments. |
| `step_efficiency` | Step Efficiency | Ratio of optimal steps to actual steps taken. |

## 3. Aggregate Denominators & Missing Data Handling

EvalForge20 never reports missing tokens or unmeasured costs as zero:
- `pass_rate` = `passed_cases / (total_cases - skipped_cases)`
- `mean_latency_ms` = average duration across successful cases only.
- `p95_latency_ms` = computed only when at least 5 valid observations exist.
- Skipped cases (due to missing ground truth) are tracked explicitly under `skipped_cases` and listed in report limitations.
