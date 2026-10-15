# EvalForge20 RAG Evaluation

## 1. Retrieval Stage Evaluation

EvalForge20 decouples retrieval stage benchmarking from answer generation quality.

### Retrieval Metrics
1. **Context Precision @ K (`context_precision_at_k`)**:
   Proportion of retrieved chunks in top K that are in `ground_truth_doc_ids`.
   $$\text{Precision@K} = \frac{|\text{Retrieved}_{1..K} \cap \text{GroundTruth}|}{K}$$

2. **Context Recall @ K (`context_recall_at_k`)**:
   Proportion of all ground truth documents retrieved in top K.
   $$\text{Recall@K} = \frac{|\text{Retrieved}_{1..K} \cap \text{GroundTruth}|}{|\text{GroundTruth}|}$$

3. **Hit Rate @ K (`hit_rate_at_k`)**:
   $1.0$ if at least one relevant document is present in the top $K$, else $0.0$.

4. **Reciprocal Rank @ K (`mrr_at_k`)**:
   $\frac{1}{\text{rank}}$ of the first relevant document retrieved in top $K$, or $0.0$ if none found.

## 2. Generation Stage Evaluation

1. **Groundedness Overlap (`groundedness_overlap`)**:
   Deterministic token overlap between the generated model response and the retrieved context passages.
   Ensures the model is not hallucinating external ungrounded claims.

## 3. Running RAG Evaluations

Example test case in JSONL:
```json
{
  "id": "rag-01",
  "input": "Where is the Eiffel Tower?",
  "expected_output": "Paris, France",
  "metadata": {
    "retrieved_chunks": [
      {"doc_id": "doc_1", "text": "The Eiffel Tower is located on the Champ de Mars in Paris."},
      {"doc_id": "doc_2", "text": "Tokyo Tower is in Minato, Tokyo."}
    ],
    "ground_truth_doc_ids": ["doc_1"],
    "k": 2
  }
}
```

CLI execution:
```bash
evalforge20 evaluate \
  --dataset examples/datasets/rag.jsonl \
  --provider mock \
  --model echo \
  --metrics context_precision_at_k,hit_rate_at_k,groundedness_overlap
```
