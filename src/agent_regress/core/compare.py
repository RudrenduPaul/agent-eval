"""Main compare() function: the primary public API entry point."""

from __future__ import annotations

import warnings
from typing import Any

import numpy as np

from agent_regress.core.report import Report, Verdict
from agent_regress.core.runner import (
    AgentCallable,
    AsyncAgentCallable,
    ScorerCallable,
    concurrent_cancellation_probe,
    run_suite,
)
from agent_regress.stats.bootstrap import bootstrap_mean_ci
from agent_regress.stats.effect_size import cohens_d
from agent_regress.stats.mann_whitney import mann_whitney_u

_MIN_N_WARN = 50


def _low_n_warning(n_a: int, n_b: int, min_n: int = _MIN_N_WARN) -> list[str]:
    """Build (and emit) the shared "insufficient samples" warning.

    Factored out of `compare()` so `compare_liveness()` can reuse the exact
    same low-n warning behavior instead of reimplementing it.
    """
    warn_msgs: list[str] = []
    if n_a < min_n or n_b < min_n:
        msg = (
            f"n_a={n_a}, n_b={n_b}: insufficient for 80% power at small effect "
            f"(d=0.2). Run at least {min_n} per version for reliable results."
        )
        warn_msgs.append(msg)
        warnings.warn(msg, UserWarning, stacklevel=3)
    return warn_msgs


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
    warn_msgs.extend(_low_n_warning(n_a, n_b))

    mw = mann_whitney_u(scores_a, scores_b, _warn=False)
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
        p_threshold=p_threshold,
        min_effect=min_effect,
        warnings=warn_msgs,
    )


async def compare_liveness(  # noqa: PLR0913
    agent_a: AsyncAgentCallable,
    agent_b: AsyncAgentCallable,
    test_case: dict[str, Any],
    n_concurrent: int = 20,
    cancel_fraction: float = 0.3,
    n_trials: int = 30,
    p_threshold: float = 0.05,
    min_effect: float = 0.2,
    n_bootstrap: int = 1000,
) -> Report:
    """Statistical regression testing for async batch-queue liveness.

    `compare()` (and `run_suite`/`arun_suite` underneath it) samples each
    call to an agent independently, so it can never reach a class of bug
    where a shared async batch queue/session gets permanently poisoned by a
    cancelled future while other concurrent callers are still waiting on it
    -- `concurrent_cancellation_probe()` exists to reach that bug for a
    *single* batch, but nothing turned repeated probe runs into a
    statistically-grounded `Report` the way `compare()` does for scalar
    scores. `compare_liveness()` closes that gap: it runs
    `concurrent_cancellation_probe(agent, test_case, n_concurrent,
    cancel_fraction)` `n_trials` times per agent, reduces each trial's
    `{"completed", "cancelled", "failed"}` dict to a single liveness score
    (`completed / n_concurrent` -- did the un-cancelled majority of the
    batch complete successfully), and feeds the two resulting lists of
    per-trial scores through the exact same `mann_whitney_u()` /
    `bootstrap_mean_ci()` / `cohens_d()` pipeline `compare()` uses, with the
    same `Verdict` thresholding.

    A poisoned/permanently-stuck queue drives `completed / n_concurrent`
    toward 0 even for tasks that were never themselves cancelled, so this
    score is sensitive to liveness bugs that a purely per-task
    completed-vs-cancelled-vs-failed count would miss.

    Args:
        agent_a: Baseline async agent under test.
        agent_b: Candidate async agent under test.
        test_case: A single test-case dict passed to every concurrent call
            within every trial, for both agents (same semantics as
            `concurrent_cancellation_probe`'s `test_case`).
        n_concurrent: Number of concurrent calls fired per trial. Passed
            straight through to `concurrent_cancellation_probe`.
        cancel_fraction: Fraction of the `n_concurrent` calls to cancel per
            trial. Passed straight through to `concurrent_cancellation_probe`.
        n_trials: Number of independent probe trials to run per agent. Each
            trial's `completed / n_concurrent` becomes one sample in that
            agent's score distribution -- this plays the same role `n_runs`
            plays in `compare()`.
        p_threshold: Same semantics as `compare()`'s `p_threshold`.
        min_effect: Same semantics as `compare()`'s `min_effect`.
        n_bootstrap: Same semantics as `compare()`'s `n_bootstrap`.

    Returns:
        A `Report` with `metric="liveness"`, built via the same statistical
        pipeline and `Verdict` logic `compare()` uses:
        `INSUFFICIENT_DATA` if either side has fewer than 10 trials, else
        `REGRESSED`/`IMPROVED`/`STABLE` by the same p-value/effect-size
        thresholding.
    """
    if n_trials < 1:
        raise ValueError(f"n_trials must be >= 1, got {n_trials}")
    if not (0.0 < p_threshold < 1.0):
        raise ValueError(f"p_threshold must be in (0, 1), got {p_threshold}")
    if min_effect < 0.0:
        raise ValueError(f"min_effect must be >= 0, got {min_effect}")

    async def _liveness_scores(agent: AsyncAgentCallable) -> list[float]:
        scores: list[float] = []
        for _ in range(n_trials):
            counts = await concurrent_cancellation_probe(
                agent, test_case, n_concurrent, cancel_fraction
            )
            scores.append(counts["completed"] / n_concurrent)
        return scores

    scores_a = await _liveness_scores(agent_a)
    scores_b = await _liveness_scores(agent_b)

    n_a, n_b = len(scores_a), len(scores_b)
    warn_msgs = _low_n_warning(n_a, n_b)

    mw = mann_whitney_u(scores_a, scores_b, _warn=False)
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
        metric="liveness",
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
        p_threshold=p_threshold,
        min_effect=min_effect,
        warnings=warn_msgs,
    )
