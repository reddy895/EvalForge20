"""Robust JSONL dataset importer with validation and line-level error isolation."""

import json
from typing import List, Tuple

from src.evalforge.schemas.dataset import RowImportError, TestCaseCreate


def parse_jsonl_content(content: str) -> Tuple[List[TestCaseCreate], List[RowImportError]]:
    """Parse JSONL lines into validated TestCaseCreate models, isolating corrupt rows."""
    valid_cases: List[TestCaseCreate] = []
    errors: List[RowImportError] = []

    lines = content.splitlines()
    for line_idx, raw_line in enumerate(lines, start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue

        try:
            data = json.loads(line)
            if not isinstance(data, dict):
                errors.append(
                    RowImportError(
                        line=line_idx,
                        raw_data=line[:100],
                        error="JSON line must be a JSON object/dictionary",
                    )
                )
                continue

            # Extract prompt with common naming aliases
            prompt = (
                data.get("prompt")
                or data.get("input")
                or data.get("question")
                or data.get("instruction")
            )
            if not prompt or not str(prompt).strip():
                errors.append(
                    RowImportError(
                        line=line_idx,
                        raw_data=line[:100],
                        error="Missing required 'prompt' (or 'input'/'question') field",
                    )
                )
                continue

            # Target answer aliases
            expected = (
                data.get("expected_output")
                or data.get("target")
                or data.get("answer")
                or data.get("ground_truth")
                or data.get("expected")
            )
            if expected is not None:
                expected = str(expected)

            context = data.get("context") or data.get("document") or data.get("reference")
            if context is not None:
                context = str(context)

            tags = data.get("tags") or []
            if isinstance(tags, str):
                tags = [t.strip() for t in tags.split(",") if t.strip()]
            elif not isinstance(tags, list):
                tags = []

            metadata = data.get("metadata") or {}
            if not isinstance(metadata, dict):
                metadata = {"raw_metadata": str(metadata)}

            eval_config = data.get("evaluator_config") or {}
            if not isinstance(eval_config, dict):
                eval_config = {}

            test_case = TestCaseCreate(
                prompt=str(prompt).strip(),
                expected_output=expected,
                context=context,
                tags=tags,
                metadata=metadata,
                evaluator_config=eval_config,
            )
            valid_cases.append(test_case)

        except json.JSONDecodeError as exc:
            errors.append(
                RowImportError(
                    line=line_idx,
                    raw_data=line[:100],
                    error=f"Malformed JSON: {exc}",
                )
            )
        except Exception as exc:
            errors.append(
                RowImportError(
                    line=line_idx,
                    raw_data=line[:100],
                    error=f"Validation failed: {exc}",
                )
            )

    return valid_cases, errors
