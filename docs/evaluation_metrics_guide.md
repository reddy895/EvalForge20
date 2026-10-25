# EvalForge20 — Evaluation Metrics, Evaluators & Scoring Rubrics Guide

This guide documents the mathematical formulas, scoring rubrics, evaluator behaviors, and state definitions implemented in the EvalForge20 evaluation engine.

---

## 1. Supported Evaluator Types

EvalForge20 provides deterministic, code-execution, and model-graded evaluators. Each evaluator implements a strictly defined contract returning a score in `[0.0, 1.0]`, a boolean `passed` flag, and granular diagnostic details.

### 1.1 Exact Match (`exact_match`)
- **Description**: Strict byte-for-byte string equality between model output and ground truth reference.
- **Formula**:
  $$\text{Score} = \begin{cases} 1.0 & \text{if } \text{prediction} = \text{reference} \\ 0.0 & \text{otherwise} \end{cases}$$
- **Threshold**: Requires `score == 1.0` to pass.

### 1.2 Normalized Exact Match (`normalized_exact_match`)
- **Description**: String equality after Unicode normalization, lowercasing, and stripping leading/trailing whitespace and punctuation.
- **Formula**:
  $$\text{Score} = \begin{cases} 1.0 & \text{if } \text{normalize}(\text{prediction}) = \text{normalize}(\text{reference}) \\ 0.0 & \text{otherwise} \end{cases}$$

### 1.3 Token F1 (`token_f1`)
- **Description**: Harmonic mean of token-level precision and recall, matching standard SQuAD QA evaluation.
- **Formula**:
  $$\text{Precision} = \frac{|\text{Tokens}_{\text{pred}} \cap \text{Tokens}_{\text{ref}}|}{|\text{Tokens}_{\text{pred}}|}, \quad \text{Recall} = \frac{|\text{Tokens}_{\text{pred}} \cap \text{Tokens}_{\text{ref}}|}{|\text{Tokens}_{\text{ref}}|}$$
  $$\text{F1} = \frac{2 \times \text{Precision} \times \text{Recall}}{\text{Precision} + \text{Recall}}$$
- **Default Threshold**: $\ge 0.80$.

### 1.4 Code Execution (`code_execution`)
- **Description**: Executes the model-generated Python function against test assertions in an isolated process sandbox.
- **Formula**:
  - `score = 1.0` if the code parses, executes within timeout (5s), and all test assertions succeed without exception.
  - `score = 0.0` if syntax error occurs, assertion fails, or runtime error occurs.

### 1.5 Numeric Tolerance (`numeric_tolerance`)
- **Description**: Extracts the final numerical answer and checks if it falls within relative epsilon ($\epsilon_{rel}$) or absolute epsilon ($\epsilon_{abs}$) bounds.
- **Formula**:
  $$|\text{pred} - \text{ref}| \le \max(\epsilon_{abs}, \epsilon_{rel} \times |\text{ref}|)$$
- **Default Epsilon**: $\epsilon_{abs} = 10^{-4}, \epsilon_{rel} = 10^{-3}$.

### 1.6 Levenshtein Similarity (`levenshtein`)
- **Description**: Normalized character edit distance.
- **Formula**:
  $$\text{Score} = 1.0 - \frac{\text{Distance}(\text{pred}, \text{ref})}{\max(|\text{pred}|, |\text{ref}|)}$$

### 1.7 LLM Judge (`llm_judge`)
- **Description**: Uses a secondary evaluator model to assess open-ended generations on a structured 1–5 rubric covering correctness, relevance, and completeness.
- **Score**: Normalized to $[0.0, 1.0]$: $\text{Score} = \frac{\text{Rating} - 1}{4}$.

---

## 2. Summary Metric Formulations

### 2.1 Pass Rate
$$\text{Pass Rate} = \frac{\sum_{i \in \text{CompletedNonErrorCases}} \mathbb{I}(\text{case}_i.\text{passed})}{|\text{CompletedNonErrorCases}|}$$
*Note*: Failed or aborted cases where inference timed out or threw an exception are tracked under `error_count` and are excluded from the pass rate denominator to prevent deflating valid test scores into synthetic zeros.

### 2.2 Latency Percentiles
Inference latencies are measured in milliseconds ($ms$) using server-side timers and provider duration telemetry.
- **Mean Latency**: $\mu = \frac{1}{N} \sum_{i=1}^N \text{latency}_i$
- **Percentiles**: P50 (median), P90, P95, and P99 computed from verified inference runs.

---

## 3. Genuine Zero vs Unavailable Metrics

EvalForge20 strictly adheres to the principle of metric fidelity:

| State | Status | Pass Rate | Latency | Display Label |
|---|---|---|---|---|
| **No Evaluations Run** | `pending` | `None` | `None` | `—` (Dash placeholder) |
| **Genuine Zero** | `completed` | `0.0` | Measured | `0% (Genuine 0)` |
| **Partial Failure** | `completed_with_errors` | Rate of non-error cases | Mean of non-error cases | `X% (with errors)` |
| **Inference Aborted** | `failed` | `None` | `None` | `Failed` |

- A score of `0%` is displayed **only** when all test cases were executed successfully and genuinely failed all validation assertions.
- Network errors, missing models, and unmeasured values are preserved as `None` / `null` and displayed with actionable status diagnostics.
