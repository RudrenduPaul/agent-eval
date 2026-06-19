"""Runs an agent callable N times on a fixed test suite."""

from __future__ import annotations

import concurrent.futures
import warnings
from collections.abc import Callable
from typing import Any

_MIN_STATISTICAL_N = 10
_MIN_RELIABLE_N = 30

AgentCallable = Callable[[dict[str, Any]], Any]
ScorerCallable = Callable[[Any, dict[str, Any]], float]


def run_suite(
    agent: AgentCallable,
    test_suite: list[dict[str, Any]],
    n_runs: int = 50,
    scorer: ScorerCallable | None = None,
    max_workers: int | None = None,
) -> list[float]:
    if not callable(agent):
        raise TypeError("agent must be callable")
    if not test_suite:
        raise ValueError("test_suite must not be empty")
    if n_runs < 1:
        raise ValueError(f"n_runs must be >= 1, got {n_runs}")

    if n_runs < _MIN_STATISTICAL_N:
        warnings.warn(
            f"n_runs={n_runs} is below the minimum for statistical validity "
            f"({_MIN_STATISTICAL_N}). "
            f"Use at least {_MIN_RELIABLE_N} runs per version for reliable results.",
            UserWarning,
            stacklevel=2,
        )

    def _to_score(raw: Any, test_case: dict[str, Any]) -> float:
        if scorer is not None:
            return float(scorer(raw, test_case))
        if isinstance(raw, (int, float)):
            return float(raw)
        raise TypeError(
            f"Agent returned {type(raw).__name__!r}. "
            "Either return a float directly or pass "
            "scorer= to convert output to float."
        )

    def _run_case(test_case: dict[str, Any]) -> list[float]:
        case_scores: list[float] = []
        for _ in range(n_runs):
            score = _to_score(agent(test_case), test_case)
            if not (0.0 <= score <= 1.0):
                warnings.warn(
                    f"Score {score:.4f} outside [0.0, 1.0]. Clamping. "
                    "Ensure your scorer returns values in [0.0, 1.0].",
                    UserWarning,
                    stacklevel=1,
                )
                score = max(0.0, min(1.0, score))
            case_scores.append(score)
        return case_scores

    all_scores: list[float] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = [pool.submit(_run_case, tc) for tc in test_suite]
        for fut in concurrent.futures.as_completed(futures):
            all_scores.extend(fut.result())

    return all_scores
