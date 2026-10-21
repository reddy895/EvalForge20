"""LLM-as-a-Judge model-assisted evaluation metric with rubric and evidence auditing."""

import json
import re
from typing import Any, Optional

from src.evalforge.evaluators.base import BaseEvaluator, MetricResult
from src.evalforge.providers.base import BaseProvider
from src.evalforge.providers.schemas import InferenceRequest


class LLMJudgeEvaluator(BaseEvaluator):
    """Model-assisted evaluator rating outputs using an LLM judge based on an explicit rubric.

    Results are explicitly flagged as estimates to distinguish them from deterministic ground truth.
    """

    name = "llm_as_judge"
    version = "1.0.0"
    is_deterministic = False

    DEFAULT_RUBRIC = """
Evaluate the response based on the following criteria:
1. Accuracy: Does the candidate answer correctly satisfy the user prompt and reference?
2. Completeness: Are all requested parts answered thoroughly?
3. Clarity: Is the explanation coherent and concise?

Score the candidate output from 1 to 5:
5 - Outstanding: Fully accurate, comprehensive, and well articulated.
4 - Good: Accurate with minor omissions.
3 - Satisfactory: Partially accurate but missing important nuances.
2 - Poor: Major inaccuracies or substantial omissions.
1 - Failure: Completely incorrect, irrelevant, or harmful.

You MUST respond strictly in the following JSON format:
{
  "score": <int 1-5>,
  "reasoning": "<concise explanation citing specific evidence>",
  "strengths": ["<strength 1>", "<strength 2>"],
  "weaknesses": ["<weakness 1>"]
}
"""

    def __init__(
        self,
        provider: BaseProvider,
        judge_model: str = "mock-llama-3.1-8b",
        rubric: Optional[str] = None,
    ):
        self.provider = provider
        self.judge_model = judge_model
        self.rubric = rubric or self.DEFAULT_RUBRIC

    async def evaluate(
        self,
        prediction: str,
        reference: Optional[str] = None,
        context: Optional[str] = None,
        rubric_override: Optional[str] = None,
        threshold: float = 0.6,  # 3/5 or higher
        **kwargs: Any,
    ) -> MetricResult:
        active_rubric = rubric_override or self.rubric

        judge_prompt = f"""[EVALUATION PROMPT]
{active_rubric}

[INPUT CONTEXT]
{context or 'N/A'}

[REFERENCE TARGET ANSWER]
{reference or 'N/A'}

[CANDIDATE OUTPUT UNDER EVALUATION]
{prediction}

Evaluate candidate output now:
"""

        req = InferenceRequest(
            model=self.judge_model,
            prompt=judge_prompt,
            temperature=0.0,
            json_schema={
                "type": "object",
                "properties": {
                    "score": {"type": "integer"},
                    "reasoning": {"type": "string"},
                },
                "required": ["score", "reasoning"],
            },
        )

        inference_resp = await self.provider.generate(req)
        raw_text = inference_resp.text

        # Parse score & reasoning
        raw_score = 3
        reasoning = raw_text
        try:
            match = re.search(r"\{[\s\S]*\}", raw_text)
            if match:
                data = json.loads(match.group(0))
                raw_score = int(data.get("score", 3))
                reasoning = data.get("reasoning", raw_text)
        except Exception:
            # Fallback regex search for digit 1-5
            digit_match = re.search(r"\b([1-5])\b", raw_text)
            if digit_match:
                raw_score = int(digit_match.group(1))

        # Normalize 1-5 scale to 0.0 - 1.0
        normalized_score = round(max(0.0, min(1.0, (raw_score - 1) / 4.0)), 2)
        passed = normalized_score >= threshold

        return MetricResult(
            name=self.name,
            score=normalized_score,
            passed=passed,
            method="llm_as_judge_estimate",
            details={
                "is_estimate": True,
                "disclaimer": "Model-generated judgment is an automated estimate, not an objective ground truth.",
                "raw_score_1_to_5": raw_score,
                "judge_model": self.judge_model,
                "judge_provider": self.provider.name,
                "reasoning": reasoning,
                "active_rubric": active_rubric[:200] + "...",
            },
        )
