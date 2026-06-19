"""Built-in scorer functions for common evaluation patterns."""

from __future__ import annotations

from typing import Any


def exact_match_scorer(output: Any, test_case: dict[str, Any]) -> float:
    expected = test_case.get("expected")
    if expected is None:
        raise KeyError(
            "test_case missing 'expected' key. "
            "Add expected values or pass a custom scorer= function."
        )
    return 1.0 if str(output).strip() == str(expected).strip() else 0.0


def f1_scorer(output: Any, test_case: dict[str, Any]) -> float:
    expected = test_case.get("expected")
    if expected is None:
        raise KeyError(
            "test_case missing 'expected' key. "
            "Add expected values or pass a custom scorer= function."
        )

    pred_tokens = set(str(output).lower().split())
    gold_tokens = set(str(expected).lower().split())

    if not pred_tokens and not gold_tokens:
        return 1.0
    if not pred_tokens or not gold_tokens:
        return 0.0

    tp = len(pred_tokens & gold_tokens)
    precision = tp / len(pred_tokens)
    recall = tp / len(gold_tokens)

    if precision + recall == 0.0:
        return 0.0
    return 2.0 * precision * recall / (precision + recall)
