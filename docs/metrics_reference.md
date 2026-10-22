# Evaluation Metrics Reference

## Deterministic Metrics
- **Exact Match (EM)**: Case-insensitive normalized string equality.
- **Token Precision, Recall, and F1**: Token-level overlap over word boundaries.
- **JSON Validity**: Verifies syntactic JSON decode without parser errors.
- **JSON Schema Compliance**: Validates required fields, types, and constraints.
- **SLA Latency**: Latency threshold compliance (e.g. < 2000ms).

## Model-Assisted Metrics
- **LLM-as-a-Judge**: Model-judged scoring with documented judge model identity.
- **Semantic Similarity**: Vector cosine similarity over sentence embeddings.
