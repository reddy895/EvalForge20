"""Local LLM-as-Judge evaluator powered by Ollama local inference."""

import json
import re

from app.config import get_settings
from app.domain.contracts import EvaluatorContract, EvaluatorInput, ProviderRequest
from app.domain.results import MetricResult
from app.evaluators.llm_judge.models import JudgeEvaluationOutput, JudgeRubric
from app.evaluators.llm_judge.rubrics import (
    ANSWER_RELEVANCE_RUBRIC,
)
from app.providers.ollama import OllamaProvider


class LocalOllamaJudgeEvaluator(EvaluatorContract):
    """Subjective evaluator utilizing a local Ollama model as a rubric-guided judge."""

    def __init__(self, rubric: JudgeRubric | None = None, judge_model: str | None = None):
        self.rubric = rubric or ANSWER_RELEVANCE_RUBRIC
        self.judge_model = judge_model

    @property
    def metric_id(self) -> str:
        return f"ollama_judge_{self.rubric.rubric_id}"

    @property
    def metric_name(self) -> str:
        return f"Ollama Judge: {self.rubric.name}"

    def _build_judge_prompt(self, eval_input: EvaluatorInput) -> tuple[str, str]:
        """Construct system prompt and user evaluation prompt based on rubric."""
        scale_desc = "\n".join(
            f"- Score {score}: {desc}"
            for score, desc in sorted(self.rubric.score_definitions.items())
        )

        system_prompt = (
            "You are an impartial, strict AI evaluation judge. Evaluate the provided system output "
            f"according to this evaluation rubric:\n\n"
            f"Criteria: {self.rubric.criteria}\n"
            f"Scoring Scale ({self.rubric.scale_min} to {self.rubric.scale_max}):\n"
            f"{scale_desc}\n\n"
            "Respond ONLY with a valid JSON object matching this exact schema:\n"
            "{\n"
            f'  "score": <number between {self.rubric.scale_min} and {self.rubric.scale_max}>,\n'
            '  "passed": <boolean>,\n'
            '  "explanation": "<concise explanation citing specific evidence>",\n'
            '  "confidence": <number between 0.0 and 1.0>\n'
            "}"
        )

        user_content_parts = [
            f"PROMPT / INPUT:\n{eval_input.case.input}\n",
            f"ACTUAL OUTPUT:\n{eval_input.actual_output or '[EMPTY OUTPUT]'}\n",
        ]
        if eval_input.case.expected_output:
            user_content_parts.append(
                f"REFERENCE / GROUND TRUTH:\n{eval_input.case.expected_output}\n"
            )

        # Include context if present
        ctx = eval_input.case.metadata.get("context")
        if ctx:
            user_content_parts.append(f"SUPPLIED CONTEXT:\n{ctx}\n")

        user_content = "\n".join(user_content_parts)
        return system_prompt, user_content

    def _extract_score_fallback(self, raw_text: str) -> JudgeEvaluationOutput:
        """Attempt robust regex recovery and JSON repair if model emitted malformed text."""
        # 1. Clean markdown code fences
        cleaned = re.sub(r"^```(?:json)?|```$", "", raw_text.strip(), flags=re.MULTILINE).strip()

        # 2. Repair common JSON errors (e.g. trailing commas)
        repaired = re.sub(r",\s*([\]}])", r"\1", cleaned)
        try:
            parsed = json.loads(repaired)
            return JudgeEvaluationOutput.model_validate(parsed)
        except Exception:
            pass

        # 3. Try finding any JSON object in text
        brace_match = re.search(r"(\{.*?\})", raw_text, re.DOTALL)
        if brace_match:
            try:
                candidate = re.sub(r",\s*([\]}])", r"\1", brace_match.group(1))
                parsed = json.loads(candidate)
                return JudgeEvaluationOutput.model_validate(parsed)
            except Exception:
                pass

        # 4. Regex search for score pattern (e.g. "score": 4 or "score": 4/5 or Score: 4)
        score_match = re.search(
            r'(?i)(?:"?score"?|rating)\s*[:=]\s*([0-9]+(?:\.[0-9]+)?)(?:/([0-9]+))?', raw_text
        )
        if score_match:
            val = float(score_match.group(1))
            passed = val >= self.rubric.pass_threshold
            # Extract explanation if available
            exp_match = re.search(r'(?i)"?explanation"?\s*[:=]\s*"([^"]+)"', raw_text)
            explanation = exp_match.group(1) if exp_match else raw_text[:200]
            return JudgeEvaluationOutput(
                score=val,
                passed=passed,
                explanation=explanation,
                confidence=0.6,
            )

        raise ValueError(f"Could not extract valid score from judge output: {raw_text[:150]}")

    async def evaluate(self, eval_input: EvaluatorInput) -> MetricResult:
        settings = get_settings()
        if not settings.enable_local_judge:
            return MetricResult(
                metric_id=self.metric_id,
                metric_name=self.metric_name,
                score=None,
                passed=None,
                reason="Local LLM judge is disabled via configuration (ENABLE_LOCAL_JUDGE=false)",
                is_model_based=True,
            )

        model_name = (
            self.judge_model
            or eval_input.options.get("judge_model")
            or settings.default_judge_model
        )
        provider = OllamaProvider(model_identifier=model_name, timeout_seconds=60.0)

        system_prompt, user_prompt = self._build_judge_prompt(eval_input)
        req = ProviderRequest(
            prompt=user_prompt,
            system_prompt=system_prompt,
            temperature=0.0,
            response_format="json",
        )

        provider_resp = await provider.generate(req)
        if not provider_resp.is_success or not provider_resp.output_text:
            return MetricResult(
                metric_id=self.metric_id,
                metric_name=self.metric_name,
                score=None,
                passed=False,
                reason=f"Judge model '{model_name}' execution failed: {provider_resp.error_message}",
                details={"error": provider_resp.error_message, "judge_model": model_name},
                is_model_based=True,
            )

        # Parse structured output
        raw_text = provider_resp.output_text.strip()
        try:
            try:
                parsed_json = json.loads(raw_text)
                judgment = JudgeEvaluationOutput.model_validate(parsed_json)
            except Exception:
                judgment = self._extract_score_fallback(raw_text)
        except Exception as exc:
            return MetricResult(
                metric_id=self.metric_id,
                metric_name=self.metric_name,
                score=None,
                passed=False,
                reason=f"Judge output could not be parsed: {exc}",
                details={"raw_output": raw_text[:300], "judge_model": model_name},
                is_model_based=True,
            )

        # Normalize score into [0.0, 1.0]
        scale_range = self.rubric.scale_max - self.rubric.scale_min
        normalized_score = (
            round((judgment.score - self.rubric.scale_min) / scale_range, 4)
            if scale_range > 0
            else 1.0
        )
        normalized_score = max(0.0, min(1.0, normalized_score))

        passed = judgment.score >= self.rubric.pass_threshold

        return MetricResult(
            metric_id=self.metric_id,
            metric_name=self.metric_name,
            score=normalized_score,
            passed=passed,
            reason=f"[{self.rubric.name}] Score {judgment.score}/{self.rubric.scale_max}: {judgment.explanation}",
            details={
                "raw_score": judgment.score,
                "normalized_score": normalized_score,
                "scale_max": self.rubric.scale_max,
                "pass_threshold": self.rubric.pass_threshold,
                "explanation": judgment.explanation,
                "confidence": judgment.confidence,
                "judge_model": model_name,
                "rubric_version": self.rubric.version,
            },
            is_model_based=True,
        )
