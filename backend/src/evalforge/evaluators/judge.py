"""Local Ollama LLM judge evaluator with rubric scoring, structured JSON output, and multi-run agreement."""

import json
import re
from typing import Any

from src.evalforge.evaluators.base import BaseEvaluator, MetricResult
from src.evalforge.providers.base import BaseProvider
from src.evalforge.providers.schemas import InferenceRequest


class LocalJudgeEvaluator(BaseEvaluator):
    """Local-first model-as-a-judge evaluator powered by an Ollama model."""

    evaluator_id: str = "judge"
    name: str = "judge"
    version: str = "1.0.0"
    is_deterministic: bool = False
    required_inputs: list[str] = ["prediction"]

    DEFAULT_RUBRIC = """Evaluate the candidate response based on accuracy, relevance, and completeness.
Score from 1 to 5:
5 - Outstanding: Completely correct, precise, and directly addresses the prompt.
4 - Good: Mostly correct with minor omissions.
3 - Satisfactory: Partially correct but lacks depth or misses key details.
2 - Poor: Major inaccuracies or substantial omissions.
1 - Failure: Completely incorrect, irrelevant, or hallucinatory.

Respond ONLY with valid JSON in this schema:
{
  "score": <int 1-5>,
  "explanation": "<concise explanation citing evidence>"
}"""

    def __init__(
        self,
        provider: BaseProvider,
        judge_model: str = "qwen2.5:3b",
        rubric: str | None = None,
        timeout_seconds: float = 30.0,
        runs: int = 1,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            name="judge",
            evaluator_id="judge",
            description="Evaluates open-ended quality using a local Ollama judge model.",
            is_deterministic=False,
            **kwargs,
        )
        self.provider = provider
        self.judge_model = judge_model
        self.rubric = rubric or self.DEFAULT_RUBRIC
        self.timeout_seconds = timeout_seconds
        self.runs = max(1, runs)

    async def evaluate(
        self,
        prediction: str,
        reference: str | None = None,
        context: str | None = None,
        rubric: str | None = None,
        **kwargs: Any,
    ) -> MetricResult:
        active_rubric = rubric or self.rubric

        prompt = f"""[RUBRIC]
{active_rubric}

[INPUT CONTEXT]
{context or "N/A"}

[REFERENCE TARGET ANSWER]
{reference or "N/A"}

[CANDIDATE OUTPUT TO EVALUATE]
{prediction}

Evaluate now. Respond ONLY with valid JSON."""

        scores: list[float] = []
        explanations: list[str] = []

        for _ in range(self.runs):
            req = InferenceRequest(
                model=self.judge_model,
                prompt=prompt,
                temperature=0.0,
                timeout=self.timeout_seconds,
            )
            try:
                resp = await self.provider.generate(req)
                score_raw, explanation = self._parse_judge_response(resp.text)
                # Normalize 1-5 score to 0.0 - 1.0 range
                norm_score = max(0.0, min(1.0, (score_raw - 1.0) / 4.0)) if score_raw is not None else 0.0
                scores.append(norm_score)
                explanations.append(explanation or "Evaluated by local judge")
            except Exception as exc:
                scores.append(0.0)
                explanations.append(f"Judge inference error: {exc}")

        avg_score = sum(scores) / len(scores) if scores else 0.0
        passed = avg_score >= 0.5  # 3/5 or higher

        # Measure judge agreement across runs
        agreement = 1.0 if len(set(scores)) <= 1 else 1.0 - (max(scores) - min(scores))

        return MetricResult(
            name=self.name,
            score=round(avg_score, 4),
            passed=passed,
            method="local_llm_judge",
            details={
                "is_judge_generated": True,
                "judge_model": self.judge_model,
                "runs_count": len(scores),
                "agreement_score": round(agreement, 4),
                "individual_scores": scores,
                "explanations": explanations,
            },
        )

    def _parse_judge_response(self, text: str) -> tuple[float | None, str | None]:
        clean = text.strip()
        fence_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", clean, re.IGNORECASE)
        if fence_match:
            clean = fence_match.group(1).strip()
        bracket_match = re.search(r"(\{[\s\S]*\})", clean)
        if bracket_match:
            clean = bracket_match.group(1).strip()

        try:
            parsed = json.loads(clean)
            if isinstance(parsed, dict):
                score = float(parsed.get("score", 0))
                expl = parsed.get("explanation") or parsed.get("reasoning")
                return score, str(expl) if expl else None
        except Exception:
            pass

        # Fallback regex search for score: X
        m = re.search(r"(?:score|rating)[\s:=]+([1-5])", clean, re.IGNORECASE)
        if m:
            return float(m.group(1)), clean[:100]

        return None, "Unable to extract numeric score from judge output"


__all__ = ["LocalJudgeEvaluator"]
