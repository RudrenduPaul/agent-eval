"""Built-in scorer functions for common evaluation patterns."""

from __future__ import annotations

from collections import Counter
from typing import Any


def _get_expected(test_case: dict[str, Any]) -> Any:
    if "expected" not in test_case:
        raise KeyError(
            "test_case missing 'expected' key. "
            "Add expected values or pass a custom scorer= function."
        )
    return test_case["expected"]


def exact_match_scorer(output: Any, test_case: dict[str, Any]) -> float:
    expected = _get_expected(test_case)
    return 1.0 if str(output).strip() == str(expected).strip() else 0.0


def f1_scorer(output: Any, test_case: dict[str, Any]) -> float:
    expected = _get_expected(test_case)

    pred_tokens = str(output).lower().split()
    gold_tokens = str(expected).lower().split()

    if not pred_tokens and not gold_tokens:
        return 1.0
    if not pred_tokens or not gold_tokens:
        return 0.0

    pred_counter = Counter(pred_tokens)
    gold_counter = Counter(gold_tokens)
    tp = sum((pred_counter & gold_counter).values())
    precision = tp / sum(pred_counter.values())
    recall = tp / sum(gold_counter.values())
    denom = precision + recall
    return 0.0 if denom == 0.0 else 2.0 * precision * recall / denom
