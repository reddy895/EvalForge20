# Local LLM-as-a-Judge Guide

EvalForge20 includes an optional rubric-guided evaluation judge powered entirely by local Ollama inference, requiring zero external evaluation frameworks or paid LLM APIs.

---

## 1. Overview & Principles

- **Local & Private:** Evaluates model outputs without sending data to external SaaS vendors.
- **Structured JSON Validation:** Strict Pydantic output validation (`score`, `passed`, `explanation`, `confidence`).
- **Resilient Parsing:** Robust recovery handles markdown fences (````json ... ````) and conversational score patterns.
- **Explicit Scoring Rubrics:** Transparent, versioned criteria prevent heuristic bias and provide human-auditable feedback.
- **Configurable:** Enabled by default, can be toggled via `ENABLE_LOCAL_JUDGE=false`.

---

## 2. Built-in Rubrics

| Metric ID | Rubric Name | Focus | Requires Reference |
|---|---|---|---|
| `ollama_judge_answer_relevance` | Answer Relevance | Prompt responsiveness, directness, conciseness | No |
| `ollama_judge_factual_correctness` | Factual Correctness | Fact checking against expected ground truth | Yes |
| `ollama_judge_context_faithfulness` | Context Faithfulness | Groundedness in supplied context (hallucination check) | No (uses metadata.context) |
| `ollama_judge_explanation_quality` | Explanation Quality | Logical coherence and step-by-step clarity | No |

---

## 3. Configuration & Usage

Set judge model and availability in `.env` or application config:
```dotenv
EVALFORGE20_ENABLE_LOCAL_JUDGE=true
EVALFORGE20_DEFAULT_JUDGE_MODEL=qwen2.5:3b
```

### In Python Code:
```python
from app.domain.contracts import EvaluatorInput
from app.evaluators.llm_judge import OllamaJudgeRelevanceEvaluator

evaluator = OllamaJudgeRelevanceEvaluator(judge_model="qwen2.5:3b")
result = await evaluator.evaluate(eval_input)

print(result.score)        # Normalized in [0.0, 1.0]
print(result.passed)       # True / False
print(result.reason)       # Rubric score explanation
print(result.details)      # raw_score, confidence, judge_model, rubric_version
```
