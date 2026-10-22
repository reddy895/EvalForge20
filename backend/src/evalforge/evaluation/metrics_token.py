"""Token-level precision, recall, and F1 score evaluator."""

import re
from collections import Counter
from dataclasses import dataclass

@dataclass
class TokenScoreResult:
    precision: float
    recall: float
    f1: float

def compute_token_f1(actual: str, expected: str) -> TokenScoreResult:
    """Compute token-level precision, recall, and F1 over whitespace/punctuation tokens."""
    def _tokenize(text: str) -> list[str]:
        return [t.lower() for t in re.findall(r"\w+", text)]

    actual_tokens = _tokenize(actual)
    expected_tokens = _tokenize(expected)

    if not actual_tokens and not expected_tokens:
        return TokenScoreResult(precision=1.0, recall=1.0, f1=1.0)
    if not actual_tokens or not expected_tokens:
        return TokenScoreResult(precision=0.0, recall=0.0, f1=0.0)

    actual_counts = Counter(actual_tokens)
    expected_counts = Counter(expected_tokens)

    common_tokens = sum((actual_counts & expected_counts).values())

    precision = common_tokens / len(actual_tokens)
    recall = common_tokens / len(expected_tokens)
    f1 = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0

    return TokenScoreResult(
        precision=round(precision, 4),
        recall=round(recall, 4),
        f1=round(f1, 4),
    )
