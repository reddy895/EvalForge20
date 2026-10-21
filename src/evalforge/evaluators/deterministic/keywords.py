"""Keyword and required/prohibited phrase matching evaluator."""

import re
from typing import Any, List, Optional

from src.evalforge.evaluators.base import BaseEvaluator, MetricResult


class KeywordEvaluator(BaseEvaluator):
    """Checks presence of required keywords and absence of prohibited phrases."""

    name = "keyword_match"
    version = "1.0.0"
    is_deterministic = True

    async def evaluate(
        self,
        prediction: str,
        reference: Optional[str] = None,
        context: Optional[str] = None,
        required_keywords: Optional[List[str]] = None,
        prohibited_keywords: Optional[List[str]] = None,
        any_keywords: Optional[List[str]] = None,
        case_sensitive: bool = False,
        **kwargs: Any,
    ) -> MetricResult:
        flags = 0 if case_sensitive else re.IGNORECASE

        req = required_keywords or []
        proh = prohibited_keywords or []
        any_k = any_keywords or []

        text = prediction if case_sensitive else prediction.lower()

        # Check prohibited keywords
        found_prohibited: List[str] = []
        for term in proh:
            pattern = re.escape(term)
            if re.search(r"\b" + pattern + r"\b", text, flags=flags):
                found_prohibited.append(term)

        # Check required keywords
        missing_required: List[str] = []
        found_required: List[str] = []
        for term in req:
            pattern = re.escape(term)
            if re.search(r"\b" + pattern + r"\b", text, flags=flags):
                found_required.append(term)
            else:
                missing_required.append(term)

        # Check any keywords
        found_any: List[str] = []
        for term in any_k:
            pattern = re.escape(term)
            if re.search(r"\b" + pattern + r"\b", text, flags=flags):
                found_any.append(term)

        # Compute score
        if found_prohibited:
            score = 0.0
            passed = False
        else:
            if req:
                score = round(len(found_required) / len(req), 4)
            else:
                score = 1.0

            if any_k and not found_any:
                passed = False
                score = min(score, 0.5)
            else:
                passed = len(missing_required) == 0

        return MetricResult(
            name=self.name,
            score=score,
            passed=passed,
            method="keyword_phrase_analysis",
            details={
                "found_required": found_required,
                "missing_required": missing_required,
                "found_prohibited": found_prohibited,
                "found_any": found_any,
                "case_sensitive": case_sensitive,
            },
        )
