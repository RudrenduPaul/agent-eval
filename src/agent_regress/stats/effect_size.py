"""Effect size calculations: Cohen's d and rank-biserial r."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

_INTERPRETATION_THRESHOLDS: tuple[tuple[float, str], ...] = (
    (0.2, "negligible"),
    (0.5, "small"),
    (0.8, "medium"),
)


@dataclass(frozen=True)
class EffectSizeResult:
    cohens_d: float
    rank_biserial_r: float
    interpretation: str


def _require_nonempty(scores_a: list[float], scores_b: list[float]) -> None:
    if not scores_a:
        raise ValueError("scores_a must not be empty")
    if not scores_b:
        raise ValueError("scores_b must not be empty")


def cohens_d(scores_a: list[float], scores_b: list[float]) -> float:
    _require_nonempty(scores_a, scores_b)

    arr_a = np.asarray(scores_a, dtype=np.float64)
    arr_b = np.asarray(scores_b, dtype=np.float64)
    n_a, n_b = len(arr_a), len(arr_b)

    # Use range (max - min) to detect constant arrays. This is exact even for
    # floats that are not exactly representable in binary (e.g. 0.3, 0.7, 0.8).
    # np.var(ddof=1) on such arrays returns a tiny non-zero value (~1e-32) due
    # to FP rounding, making pooled_std non-zero and causing the formula to
    # return a huge spurious finite number instead of ±inf.
    is_const_a = n_a <= 1 or float(arr_a.max() - arr_a.min()) == 0.0
    is_const_b = n_b <= 1 or float(arr_b.max() - arr_b.min()) == 0.0

    var_a = 0.0 if is_const_a else float(arr_a.var(ddof=1))
    var_b = 0.0 if is_const_b else float(arr_b.var(ddof=1))

    pooled_var = ((n_a - 1) * var_a + (n_b - 1) * var_b) / max(n_a + n_b - 2, 1)
    pooled_std = float(np.sqrt(pooled_var))

    if pooled_std == 0.0:
        delta = float(arr_b.mean() - arr_a.mean())
        if delta == 0.0 or n_a <= 1 or n_b <= 1:
            return 0.0
        return float(np.copysign(np.inf, delta))
    return float((arr_b.mean() - arr_a.mean()) / pooled_std)


def rank_biserial_r(scores_a: list[float], scores_b: list[float]) -> float:
    _require_nonempty(scores_a, scores_b)

    n_a, n_b = len(scores_a), len(scores_b)
    arr_a = np.asarray(scores_a, dtype=np.float64)
    arr_b = np.asarray(scores_b, dtype=np.float64)
    diff = arr_b[np.newaxis, :] - arr_a[:, np.newaxis]
    concordant = float(np.sum(diff > 0) + 0.5 * np.sum(diff == 0))
    return 2.0 * concordant / (n_a * n_b) - 1.0


def interpret_cohens_d(d: float) -> str:
    abs_d = abs(d)
    for threshold, label in _INTERPRETATION_THRESHOLDS:
        if abs_d < threshold:
            return label
    return "large"


def compute_effect_sizes(
    scores_a: list[float], scores_b: list[float]
) -> EffectSizeResult:
    d = cohens_d(scores_a, scores_b)
    r = rank_biserial_r(scores_a, scores_b)
    return EffectSizeResult(
        cohens_d=d, rank_biserial_r=r, interpretation=interpret_cohens_d(d)
    )
