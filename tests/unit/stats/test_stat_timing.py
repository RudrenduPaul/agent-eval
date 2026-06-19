"""Timing regression guard: full stats pipeline must complete < 500ms for n=1000.

This test lives in unit/ so it runs in CI even when benchmarks/ is run with
--benchmark-only (which skips non-benchmark tests).
"""

from __future__ import annotations

import random
import time

from agent_regress.stats.bootstrap import bootstrap_mean_ci
from agent_regress.stats.effect_size import compute_effect_sizes
from agent_regress.stats.mann_whitney import mann_whitney_u


def _make_scores(n: int, mean: float = 0.75, std: float = 0.08, seed: int = 42) -> list[float]:
    rng = random.Random(seed)
    return [max(0.0, min(1.0, rng.gauss(mean, std))) for _ in range(n)]


def test_stats_pipeline_under_500ms() -> None:
    a = _make_scores(1000, 0.80)
    b = _make_scores(1000, 0.72, seed=99)

    start = time.perf_counter()
    mann_whitney_u(a, b)
    bootstrap_mean_ci(a, b, n_resamples=1000)
    compute_effect_sizes(a, b)
    elapsed_ms = (time.perf_counter() - start) * 1000

    assert elapsed_ms < 500, (
        f"Statistical computation took {elapsed_ms:.1f}ms, expected < 500ms"
    )
