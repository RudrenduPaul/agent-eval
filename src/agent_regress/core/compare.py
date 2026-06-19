"""Main compare() function: the primary public API entry point."""

from __future__ import annotations

import warnings
from typing import Any

import numpy as np

from agent_regress.core.report import Report, Verdict
from agent_regress.core.runner import AgentCallable, ScorerCallable, run_suite
from agent_regress.stats.bootstrap import bootstrap_mean_ci
from agent_regress.stats.effect_size import cohens_d
from agent_regress.stats.mann_whitney import mann_whitney_u

_MIN_N_WARN = 30


def compare(  # noqa: PLR0913
    version_a: AgentCallable,
    version_b: AgentCallable,
    test_suite: list[dict[str, Any]],
    n_runs: int = 50,
    metric: str = "accuracy",
    scorer: ScorerCallable | None = None,
    p_threshold: float = 0.05,
    min_effect: float = 0.2,
    n_bootstrap: int = 1000,
    max_workers: int | None = None,
) -> Report:
    if not test_suite:
        raise ValueError("test_suite must not be empty")
    if n_runs < 1:
        raise ValueError(f"n_runs must be >= 1, got {n_runs}")
    if not (0.0 < p_threshold < 1.0):
        raise ValueError(f"p_threshold must be in (0, 1), got {p_threshold}")
    if min_effect < 0.0:
        raise ValueError(f"min_effect must be >= 0, got {min_effect}")

    warn_msgs: list[str] = []

    if scorer is None and metric == "accuracy":
        from agent_regress.core.scorer import exact_match_scorer  # noqa: PLC0415

        scorer = exact_match_scorer

    scores_a = run_suite(
        agent=version_a,
        test_suite=test_suite,
        n_runs=n_runs,
        scorer=scorer,
        max_workers=max_workers,
    )
    scores_b = run_suite(
        agent=version_b,
        test_suite=test_suite,
        n_runs=n_runs,
        scorer=scorer,
        max_workers=max_workers,
    )

    n_a, n_b = len(scores_a), len(scores_b)
    if n_a < _MIN_N_WARN or n_b < _MIN_N_WARN:
        msg = (
            f"n_a={n_a}, n_b={n_b}: insufficient for 80% power at small effect "
            f"(d=0.2). Run at least 50 per version for reliable results."
        )
        warn_msgs.append(msg)
        warnings.warn(msg, UserWarning, stacklevel=2)

    mw = mann_whitney_u(scores_a, scores_b)
    ci = bootstrap_mean_ci(scores_a, scores_b, n_resamples=n_bootstrap)
    d = cohens_d(scores_a, scores_b)

    arr_a = np.asarray(scores_a, dtype=np.float64)
    arr_b = np.asarray(scores_b, dtype=np.float64)
    std_a = float(arr_a.std(ddof=1)) if n_a > 1 else 0.0
    std_b = float(arr_b.std(ddof=1)) if n_b > 1 else 0.0

    if n_a < 10 or n_b < 10:
        verdict = Verdict.INSUFFICIENT_DATA
    elif mw.p_value < p_threshold and abs(d) >= min_effect:
        verdict = Verdict.REGRESSED if d < 0.0 else Verdict.IMPROVED
    else:
        verdict = Verdict.STABLE

    return Report(
        metric=metric,
        verdict=verdict,
        p_value=mw.p_value,
        effect_size=d,
        ci_lower=ci.lower,
        ci_upper=ci.upper,
        n_a=n_a,
        n_b=n_b,
        mean_a=float(arr_a.mean()),
        mean_b=float(arr_b.mean()),
        std_a=std_a,
        std_b=std_b,
        mean_delta=ci.mean_delta,
        warnings=warn_msgs,
    )
