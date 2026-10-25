"""Isolated test-case executor with metric scoring and error capture."""

from typing import Any

from src.evalforge.core.logging import get_logger
from src.evalforge.evaluators.base import BaseEvaluator
from src.evalforge.evaluators.deterministic.code_execution import CodeExecutionEvaluator
from src.evalforge.evaluators.deterministic.exact_match import (
    ExactMatchEvaluator,
    NormalizedExactMatchEvaluator,
)
from src.evalforge.evaluators.deterministic.json_schema import JsonSchemaEvaluator
from src.evalforge.evaluators.deterministic.keywords import KeywordEvaluator
from src.evalforge.evaluators.deterministic.numeric_tolerance import NumericToleranceEvaluator
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
        self.evaluators: dict[str, BaseEvaluator] = self._build_evaluators()

    def _build_evaluators(self) -> dict[str, BaseEvaluator]:
        evals: dict[str, BaseEvaluator] = {
            "exact_match": ExactMatchEvaluator(),
            "normalized_exact_match": NormalizedExactMatchEvaluator(),
            "token_f1": TokenF1Evaluator(),
            "keyword_match": KeywordEvaluator(),
            "json_schema": JsonSchemaEvaluator(),
            "code_execution": CodeExecutionEvaluator(),
            "numeric_tolerance": NumericToleranceEvaluator(),
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
            timeout=self.config.timeout_seconds,
        )

        # Attach json schema if specified in case evaluator config
        case_cfg = case.evaluator_config or {}
        assertion_type = (
            case_cfg.get("assertion_type")
            or case.metadata.get("assertion_type")
            or "exact_match"
        )
        if "json_schema" in case_cfg or assertion_type == "json_schema":
            inference_req.json_schema = case_cfg.get("json_schema") or {"type": "object"}

        resp = None
        try:
            resp = await self.provider.generate(inference_req)
            pred_text = resp.text
            latency_ms = resp.latency_ms
            usage_dict = resp.usage.model_dump() if resp.usage else {}
            if resp.raw_metadata:
                for k, v in resp.raw_metadata.items():
                    if v is not None:
                        usage_dict[k] = v
            error_msg = None
        except Exception as exc:
            logger.warning("Inference failed for case '%s': %s", case.id, exc)
            pred_text = ""
            latency_ms = None
            usage_dict = None
            error_msg = str(exc)

        # Compute metrics
        metrics_dict: dict[str, Any] = {
            "_assertion_type": assertion_type,
            "_latency_ms": latency_ms,
        }
        if resp and resp.raw_metadata:
            metrics_dict["_tokens_per_second"] = resp.raw_metadata.get("tokens_per_second")
            metrics_dict["_load_duration_ms"] = resp.raw_metadata.get("load_duration_ms")

        # Dynamically determine metrics to evaluate
        metrics_to_run = list(self.config.metrics)
        if assertion_type in self.evaluators and assertion_type not in metrics_to_run:
            metrics_to_run.append(assertion_type)

        all_passed = error_msg is None

        for metric_name in metrics_to_run:
            evaluator = self.evaluators.get(metric_name)
            if error_msg is not None:
                metrics_dict[metric_name] = {
                    "name": metric_name,
                    "score": None,
                    "passed": False,
                    "method": "inference_error",
                    "details": {"error": error_msg},
                }
                all_passed = False
            elif evaluator:
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
                        "score": None,
                        "passed": False,
                        "method": "evaluation_error",
                        "details": {"error": str(eval_exc)},
                    }
                    all_passed = False

        if assertion_type and assertion_type not in metrics_dict:
            metrics_dict[assertion_type] = {
                "name": assertion_type,
                "score": 1.0 if all_passed else 0.0,
                "passed": all_passed,
                "method": "assertion_check",
                "details": {"error": error_msg} if error_msg else {},
            }

        # Case pass/fail is determined by the specific target assertion
        case_passed = error_msg is None
        case_error = error_msg
        if error_msg is not None:
            case_passed = False
        elif assertion_type in metrics_dict and isinstance(metrics_dict[assertion_type], dict):
            case_passed = bool(metrics_dict[assertion_type].get("passed", False))
            assertion_details = metrics_dict[assertion_type].get("details") or {}
            if not case_passed and not case_error and assertion_details.get("error"):
                case_error = str(assertion_details.get("error"))
        else:
            case_passed = all_passed

        case_res = CaseResult(
            evaluation_id=evaluation_id,
            case_id=case.id,
            prompt=case.prompt,
            expected_output=case.expected_output,
            actual_output=pred_text,
            passed=case_passed,
            latency_ms=latency_ms,
            error_message=case_error,
        )
        case_res.metrics = metrics_dict
        if usage_dict:
            case_res.token_usage = usage_dict

        return case_res
