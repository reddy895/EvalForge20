# EvalForge20 — Evaluation Metrics Specification & Methodology

This document specifies the exact definitions, mathematical formulas, units, aggregation rules, and missing-value behaviors used across EvalForge20.

---

## 1. Performance & Telemetry Metrics

All performance metrics originate directly from verified execution measurements reported by the inference engine (e.g., Ollama's daemon API or high-resolution OS monotonic timers). Missing values are represented as `null`, never artificially defaulted to `0.0`.

### A. End-to-End Latency
- **Symbol / Field**: `latency_ms`
- **Definition**: Total wall-clock elapsed time from request dispatch until complete response receipt.
- **Unit**: Milliseconds (`ms`)
- **Measurement Source**:
  - Primary (Ollama): `total_duration` reported in nanoseconds, converted via:
    $$\text{latency\_ms} = \frac{\text{total\_duration\_ns}}{10^6}$$
  - Fallback: High-resolution monotonic timer `time.perf_counter() * 1000.0`.
- **Missing Value Handling**: Preserved as `null` or excluded from positive latency calculations. Failed requests (`error_message is not None`) do not introduce `0.0 ms` artifacts into latency percentiles.

### B. Output Generation Throughput (Tokens per Second)
- **Symbol / Field**: `tokens_per_second` (or `avg_tokens_per_second`)
- **Definition**: Number of output completion tokens generated divided by the duration spent in the model's generation/evaluation phase.
- **Unit**: Tokens per second (`tok/s`)
- **Formula**:
  $$\text{tokens\_per\_second} = \frac{\text{eval\_count}}{\text{eval\_duration\_ns} / 10^9}$$
- **Validity Guard**: Computed only when `eval_count > 0` and `eval_duration_ns > 0`. Throughput is **never** inferred from token counts without valid duration telemetry.

### C. Model Load Duration
- **Symbol / Field**: `load_duration_ms`
- **Definition**: Time spent by the local runtime loading model weights from disk into host RAM / VRAM before prompt ingestion.
- **Unit**: Milliseconds (`ms`)
- **Formula**:
  $$\text{load\_duration\_ms} = \frac{\text{load\_duration\_ns}}{10^6}$$

### D. Prompt Evaluation Throughput
- **Symbol / Field**: `prompt_tokens_per_second`
- **Definition**: Speed at which input prompt tokens are encoded and processed.
- **Formula**:
  $$\text{prompt\_tokens\_per\_second} = \frac{\text{prompt\_eval\_count}}{\text{prompt\_eval\_duration\_ns} / 10^9}$$

---

## 2. Deterministic Accuracy & Quality Metrics

Deterministic evaluators produce objective, reproducible boolean (`passed`) and numerical (`score` $\in [0.0, 1.0]$) outputs without stochastic variance.

### A. Strict Exact Match
- **Name**: `exact_match`
- **Method**: `strict_string_equality`
- **Definition**: Character-for-character equality after trimming outer whitespace.
- **Formula**:
  $$\text{score} = \begin{cases} 1.0 & \text{if } \text{strip}(\hat{y}) = \text{strip}(y^*) \\ 0.0 & \text{otherwise} \end{cases}$$

### B. Normalized Exact Match
- **Name**: `normalized_exact_match`
- **Method**: `normalized_text_equality`
- **Definition**: Equality after case-folding, punctuation removal, article stripping (`a`, `an`, `the`), and whitespace collapse.

### C. Token Precision, Recall, and F1
- **Name**: `token_f1`
- **Method**: `token_overlap_f1`
- **Formulas**:
  $$\text{Precision} = \frac{|\hat{T} \cap T^*|}{|\hat{T}|}, \quad \text{Recall} = \frac{|\hat{T} \cap T^*|}{|T^*|}, \quad F_1 = \frac{2 \cdot \text{Precision} \cdot \text{Recall}}{\text{Precision} + \text{Recall}}$$
- **Passing Condition**: $F_1 \ge 0.70$ (configurable threshold).

### D. JSON Schema Compliance
- **Name**: `json_schema_compliance`
- **Method**: `json_schema_validation`
- **Definition**:
  1. Prediction string must parse into valid JSON syntax (markdown fences stripped).
  2. Required top-level keys must all be present.
  3. Primitive types (string, integer, boolean, list, object) must conform to schema declarations.

### E. Keyword Presence & Prohibition
- **Name**: `keyword_match`
- **Method**: `keyword_word_boundary_match`
- **Rules**:
  - Any prohibited keyword present $\implies \text{score} = 0.0$, `passed = False`.
  - Required keywords scored proportionally: $\frac{|\text{found}|}{|\text{required}|}$.

---

## 3. Model-Assisted & Heuristic Quality Metrics

Model-assisted metrics are **explicitly flagged as estimates** (`is_estimate: true`) with documented judge provenance and disclaimers.

### A. LLM-as-a-Judge
- **Name**: `llm_as_judge`
- **Method**: `llm_as_judge_estimate`
- **Disclaimer**: *"Model-generated judgment is an automated estimate, not an objective ground truth."*
- **Scoring**: Explicit rubric rated from 1 to 5, normalized via:
  $$\text{score} = \frac{\text{raw\_score} - 1}{4}$$
- **Passing Threshold**: Normalized score $\ge 0.60$ (rating $\ge 3/5$).

### B. Semantic N-Gram Similarity
- **Name**: `semantic_similarity`
- **Method**: `ngram_jaccard_similarity`
- **Formula**:
  $$\text{score} = 0.6 \cdot J_{\text{unigram}} + 0.4 \cdot J_{\text{bigram}}$$
  where $J(A, B) = \frac{|A \cap B|}{|A \cup B|}$.

---

## 4. Reliability & Error Metrics

EvalForge20 tracks system stability to distinguish provider connection issues from evaluation assertion failures.

- **`error_count`**: Total test cases that failed due to runtime exceptions rather than incorrect answers.
- **`timeout_count`**: Total requests that exceeded client or provider deadlines.
- **`error_categories`**: Structured dictionary grouping errors into:
  - `timeout`: Exceeded inference time limits.
  - `connection_error`: Ollama daemon unreachable or socket refused.
  - `model_not_found`: Requested model tag not pulled or installed.
  - `schema_validation_error`: Invalid payload formatting.
  - `inference_error`: Generic model runtime failure.

---

## 5. Statistical Aggregation Rules

When aggregating results across $N$ test cases:

- **Pass Rate**:
  $$\text{pass\_rate} = \frac{\sum_{i=1}^N \mathbb{I}(\text{passed}_i)}{N}$$
- **Percentiles ($P_{10}, P_{25}, P_{50}, P_{75}, P_{90}, P_{95}, P_{99}$)**:
  Computed using standard linear interpolation between data points of sorted valid observations.
- **Missing Value Policy**:
  If a metric cannot be collected (e.g. `tokens_per_second` on an inference error), it is omitted from the sample pool rather than populated with zero.
