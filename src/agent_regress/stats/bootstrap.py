"""Bootstrap confidence intervals on score distribution deltas."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class BootstrapCI:
    lower: float
    upper: float
    mean_delta: float
    n_resamples: int
    confidence: float


def bootstrap_mean_ci(
    scores_a: list[float],
    scores_b: list[float],
    n_resamples: int = 1000,
    confidence: float = 0.95,
    seed: int | None = 42,
) -> BootstrapCI:
    if not scores_a:
        raise ValueError("scores_a must not be empty")
    if not scores_b:
        raise ValueError("scores_b must not be empty")
    if n_resamples < 100:
        raise ValueError(f"n_resamples must be >= 100, got {n_resamples}")
    if not (0.0 < confidence < 1.0):
        raise ValueError(f"confidence must be in (0, 1), got {confidence}")

    rng = np.random.default_rng(seed)
    arr_a = np.asarray(scores_a, dtype=np.float64)
    arr_b = np.asarray(scores_b, dtype=np.float64)

    resamples_a = rng.choice(arr_a, size=(n_resamples, len(arr_a)), replace=True)
    resamples_b = rng.choice(arr_b, size=(n_resamples, len(arr_b)), replace=True)
    deltas = resamples_b.mean(axis=1) - resamples_a.mean(axis=1)

    alpha = 1.0 - confidence
    lower = float(np.quantile(deltas, alpha / 2.0))
    upper = float(np.quantile(deltas, 1.0 - alpha / 2.0))
    mean_delta = float(arr_b.mean() - arr_a.mean())

    return BootstrapCI(
        lower=lower,
        upper=upper,
        mean_delta=mean_delta,
        n_resamples=n_resamples,
        confidence=confidence,
    )
