# EvalForge20 Dataset Specification

## 1. Overview

EvalForge20 datasets are serialized as standard JSON Lines (`.jsonl`) files where each non-empty line represents a discrete `EvaluationCase`.

## 2. Schema Specification

Each line in a dataset must adhere to the following JSON structure:

```json
{
  "id": "case-001",
  "input": "What is the capital of France?",
  "expected_output": "Paris",
  "category": "geography",
  "tags": ["europe", "capitals"],
  "metadata": {
    "difficulty": "easy",
    "source": "curated-qa"
  }
}
```

### Fields

| Field | Type | Required | Description |
|---|---|---|---|
| `id` | `string` | **Yes** | Unique identifier within the dataset. Whitespace is stripped. |
| `input` | `string` | **Yes** | Task prompt or user input sent to the target model/agent. |
| `expected_output` | `string \| null` | No | Reference answer or ground truth. Optional for unsupervised or format-only metrics. |
| `category` | `string \| null` | No | Category used for slice-based performance aggregation. |
| `tags` | `array[string]` | No | Labels for searching and filtering cases. |
| `metadata` | `object` | No | Arbitrary contextual data (e.g. RAG retrieved passages, agent trajectories). |

## 3. RAG and Agent Context in Datasets

### RAG Example
```json
{
  "id": "rag-001",
  "input": "How does photosynthesis work?",
  "expected_output": "Plants convert sunlight, carbon dioxide, and water into glucose and oxygen.",
  "metadata": {
    "retrieved_chunks": [
      {"doc_id": "chunk_bio_1", "text": "Photosynthesis is the process by which green plants transform light energy..."},
      {"doc_id": "chunk_bio_2", "text": "Unrelated passage..."}
    ],
    "ground_truth_doc_ids": ["chunk_bio_1"],
    "k": 2
  }
}
```

### Agent Example
```json
{
  "id": "agent-001",
  "input": "Calculate 15 multiplied by 4",
  "expected_output": "60",
  "metadata": {
    "expected_tools": ["calculator"],
    "expected_arguments": {"calculator": ["a", "b", "op"]},
    "optimal_steps": 1,
    "max_steps": 3
  }
}
```

## 4. Hashing and Versioning

EvalForge20 calculates a deterministic SHA-256 hash across canonicalized case representations:
- Normalizes JSON keys in alphabetical order.
- Line order is preserved.
- If two datasets have identical test cases in the same order, their `version_hash` will match exactly.
