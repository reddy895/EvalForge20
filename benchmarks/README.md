# EvalForge20 Benchmarks Specification

EvalForge20 provides reproducible, deterministic benchmark datasets and task definitions for rigorous local and offline LLM evaluation.

## Tasks Directory (`benchmarks/tasks/`)
- `coding.json`: Python function synthesis and algorithms with syntax validation.
- `structured.json`: Strict JSON schema compliance, key presence, and constraint validation.
- `reasoning.json`: Arithmetic reasoning, logic puzzles, and symbolic calculation.

## Datasets Directory (`benchmarks/datasets/`)
Datasets contain test cases formatted as:
```json
[
  {
    "id": "code_01",
    "prompt": "Write a Python function named ...",
    "expected_output": "def ...",
    "task_category": "coding",
    "assertions": ["syntax_valid", "exact_match"]
  }
]
```

## Adding Custom Benchmarks
1. Add a JSON dataset array into `benchmarks/datasets/<name>.json`.
2. Define the task configuration in `benchmarks/tasks/<name>.json`.
3. The benchmark will automatically register in the `BenchmarkService` and appear on the web frontend.
