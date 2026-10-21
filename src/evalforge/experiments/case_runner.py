"""Isolated test-case executor with metric scoring and error capture."""

from typing import Any, Dict, List, Optional

from src.evalforge.core.logging import get_logger
from src.evalforge.evaluators.base import BaseEvaluator
from src.evalforge.evaluators.deterministic.exact_match import ExactMatchEvaluator
from src.evalforge.evaluators.deterministic.json_schema import JsonSchemaEvaluator
from src.evalforge.evaluators.deterministic.keywords import KeywordEvaluator
from src.evalforge.evaluators.deterministic.token_f1 import TokenF1Evaluator
from src.evalforge.evaluators.llm_judge import LLMJudgeEvaluator
from src.evalforge.evaluators.semantic import SemanticSimilarityEvaluator
from src.evalforge.experiments.snapshot import FrozenTestCase
from src.evalforge.providers.base import BaseProvider
from src.evalforge.providers.schemas import InferenceRequest
from src.evalforge.schemas.evaluation import EvaluationConfig
from src.evalforge.storage.models.evaluation import CaseResult

logger = get_logger("evalforge.experiments.case_runner")


class CaseRunner:
    """Executes a single test case against an inference provider and evaluates all configured metrics."""

    def __init__(
        self,
        provider: BaseProvider,
        model_id: str,
        config: EvaluationConfig,
    ):
        self.provider = provider
        self.model_id = model_id
        self.config = config
        self.evaluators: Dict[str, BaseEvaluator] = self._build_evaluators()

    def _build_evaluators(self) -> Dict[str, BaseEvaluator]:
        evals: Dict[str, BaseEvaluator] = {
            "exact_match": ExactMatchEvaluator(),
            "token_f1": TokenF1Evaluator(),
            "keyword_match": KeywordEvaluator(),
            "json_schema": JsonSchemaEvaluator(),
            "semantic_similarity": SemanticSimilarityEvaluator(),
        }
        # Model judge if enabled in metrics
        if "llm_as_judge" in self.config.metrics:
            judge_model = self.config.judge_model or self.model_id
            evals["llm_as_judge"] = LLMJudgeEvaluator(
                provider=self.provider,
                judge_model=judge_model,
                rubric=self.config.rubric,
            )
        return evals

    async def execute_case(self, case: FrozenTestCase, evaluation_id: str) -> CaseResult:
        """Run candidate model on test case and calculate all metric scores."""
        inference_req = InferenceRequest(
            model=self.model_id,
            prompt=case.prompt,
            temperature=self.config.temperature,
            top_p=self.config.top_p,
            seed=self.config.seed,
            max_tokens=self.config.max_tokens,
            context_length=self.config.context_length,
            stop=self.config.stop,
        )

        # Attach json schema if specified in case evaluator config
        case_cfg = case.evaluator_config or {}
        if "json_schema" in case_cfg:
            inference_req.json_schema = case_cfg["json_schema"]

        try:
            resp = await self.provider.generate(inference_req)
            pred_text = resp.text
            latency_ms = resp.latency_ms
            usage_dict = resp.usage.model_dump() if resp.usage else None
            error_msg = None
        except Exception as exc:
            logger.warning("Inference failed for case '%s': %s", case.id, exc)
            pred_text = ""
            latency_ms = 0.0
            usage_dict = None
            error_msg = str(exc)

        # Compute metrics
        metrics_dict: Dict[str, Any] = {}
        all_passed = error_msg is None

        for metric_name in self.config.metrics:
            evaluator = self.evaluators.get(metric_name)
            if evaluator and error_msg is None:
                try:
                    metric_res = await evaluator.evaluate(
                        prediction=pred_text,
                        reference=case.expected_output,
                        context=case.context,
                        **case_cfg,
                    )
                    metrics_dict[metric_name] = metric_res.model_dump()
                    if not metric_res.passed:
                        all_passed = False
                except Exception as eval_exc:
                    logger.warning("Metric '%s' computation error: %s", metric_name, eval_exc)
                    metrics_dict[metric_name] = {
                        "name": metric_name,
                        "score": 0.0,
                        "passed": False,
                        "method": "evaluation_error",
                        "details": {"error": str(eval_exc)},
                    }
                    all_passed = False

        case_res = CaseResult(
            evaluation_id=evaluation_id,
            case_id=case.id,
            prompt=case.prompt,
            expected_output=case.expected_output,
            actual_output=pred_text,
            passed=all_passed,
            latency_ms=latency_ms,
            error_message=error_msg,
        )
        case_res.metrics = metrics_dict
        if usage_dict:
            case_res.token_usage = usage_dict

        return case_res
