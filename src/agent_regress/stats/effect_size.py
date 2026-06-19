"""Effect size calculations: Cohen's d and rank-biserial r."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class EffectSizeResult:
    cohens_d: float
    rank_biserial_r: float
    interpretation: str


def cohens_d(scores_a: list[float], scores_b: list[float]) -> float:
    if not scores_a:
        raise ValueError("scores_a must not be empty")
    if not scores_b:
        raise ValueError("scores_b must not be empty")

    arr_a = np.asarray(scores_a, dtype=np.float64)
    arr_b = np.asarray(scores_b, dtype=np.float64)
    n_a, n_b = len(arr_a), len(arr_b)

    var_a = float(arr_a.var(ddof=1)) if n_a > 1 else 0.0
    var_b = float(arr_b.var(ddof=1)) if n_b > 1 else 0.0

    pooled_var = ((n_a - 1) * var_a + (n_b - 1) * var_b) / max(n_a + n_b - 2, 1)
    pooled_std = float(np.sqrt(pooled_var))

    if pooled_std == 0.0:
        delta = float(arr_b.mean() - arr_a.mean())
        if delta == 0.0 or n_a <= 1 or n_b <= 1:
            return 0.0
        return float(np.copysign(np.inf, delta))
    return float((arr_b.mean() - arr_a.mean()) / pooled_std)


def rank_biserial_r(scores_a: list[float], scores_b: list[float]) -> float:
    if not scores_a:
        raise ValueError("scores_a must not be empty")
    if not scores_b:
        raise ValueError("scores_b must not be empty")

    n_a, n_b = len(scores_a), len(scores_b)
    arr_a = np.asarray(scores_a, dtype=np.float64)
    arr_b = np.asarray(scores_b, dtype=np.float64)
    diff = arr_b[np.newaxis, :] - arr_a[:, np.newaxis]
    concordant = float(np.sum(diff > 0) + 0.5 * np.sum(diff == 0))
    return 2.0 * concordant / (n_a * n_b) - 1.0


def interpret_cohens_d(d: float) -> str:
    abs_d = abs(d)
    if abs_d < 0.2:
        return "negligible"
    elif abs_d < 0.5:
        return "small"
    elif abs_d < 0.8:
        return "medium"
    return "large"


def compute_effect_sizes(
    scores_a: list[float], scores_b: list[float]
) -> EffectSizeResult:
    d = cohens_d(scores_a, scores_b)
    r = rank_biserial_r(scores_a, scores_b)
    return EffectSizeResult(
        cohens_d=d, rank_biserial_r=r, interpretation=interpret_cohens_d(d)
    )
