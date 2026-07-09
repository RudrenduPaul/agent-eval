"""State-diff / checkpoint round-trip scorer.

Compares a reconstructed state dict (e.g. from a resumed LangGraph thread or
checkpoint round-trip) against an expected state dict, field by field.
"""

from __future__ import annotations

from typing import Any


def _dict_match_fraction(actual: dict[str, Any], expected: dict[str, Any]) -> float:
    if not expected:
        return 1.0

    matches = 0
    for key, expected_value in expected.items():
        if key not in actual:
            continue
        actual_value = actual[key]
        if isinstance(expected_value, dict) and isinstance(actual_value, dict):
            if _dict_match_fraction(actual_value, expected_value) == 1.0:
                matches += 1
        elif actual_value == expected_value:
            matches += 1

    return matches / len(expected)


def state_diff_scorer(output: Any, test_case: dict[str, Any]) -> float:
    """Score how many top-level (and nested) keys of a reconstructed state match.

    `output` is the reconstructed state dict under test; `test_case["expected_state"]`
    is the expected state dict. Returns the fraction of matching keys, recursing into
    nested dicts and comparing leaf values with `==`. Missing keys count as
    non-matches rather than raising.
    """
    if "expected_state" not in test_case:
        raise KeyError(
            "test_case missing 'expected_state' key. "
            "Add an expected_state dict or pass a custom scorer= function."
        )
    expected_state = test_case["expected_state"]

    if not isinstance(output, dict) or not isinstance(expected_state, dict):
        return 1.0 if output == expected_state else 0.0

    return _dict_match_fraction(output, expected_state)
