"""Mann-Whitney U test with continuity correction."""
from __future__ import annotations

import warnings
from dataclasses import dataclass

import numpy as np
from scipy import stats

_MIN_N_RELIABLE = 30


@dataclass(frozen=True)
class MannWhitneyResult:
    statistic: float
    p_value: float
    n_a: int
    n_b: int
    sufficient_power: bool


def mann_whitney_u(
    scores_a: list[float],
    scores_b: list[float],
    alternative: str = "two-sided",
) -> MannWhitneyResult:
    if not scores_a:
        raise ValueError("scores_a must not be empty")
    if not scores_b:
        raise ValueError("scores_b must not be empty")
    if alternative not in ("two-sided", "less", "greater"):
        raise ValueError(
            f"alternative must be 'two-sided', 'less', or 'greater', got {alternative!r}"
        )

    n_a = len(scores_a)
    n_b = len(scores_b)
    sufficient_power = n_a >= _MIN_N_RELIABLE and n_b >= _MIN_N_RELIABLE

    if not sufficient_power:
        warnings.warn(
            f"n_a={n_a}, n_b={n_b}: fewer than {_MIN_N_RELIABLE} samples per group. "
            "Statistical power may be insufficient for small effects. "
            "Use at least 50 runs per version for reliable results.",
            UserWarning,
            stacklevel=2,
        )

    arr_a = np.asarray(scores_a, dtype=np.float64)
    arr_b = np.asarray(scores_b, dtype=np.float64)
    result = stats.mannwhitneyu(arr_a, arr_b, alternative=alternative, method="auto")
    return MannWhitneyResult(
        statistic=float(result.statistic),
        p_value=float(result.pvalue),
        n_a=n_a,
        n_b=n_b,
        sufficient_power=sufficient_power,
    )
