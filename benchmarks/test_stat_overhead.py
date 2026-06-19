"""Benchmark: statistical test computation overhead.

Target: full comparison overhead stays under 500ms for n=1000 per version.
Run: uv run pytest benchmarks/test_stat_overhead.py --benchmark-only -v
"""
from __future__ import annotations

import random
import time

import pytest

from agent_regress.stats.bootstrap import bootstrap_mean_ci
from agent_regress.stats.effect_size import compute_effect_sizes
from agent_regress.stats.mann_whitney import mann_whitney_u


def _make_scores(n: int, mean: float = 0.75, std: float = 0.08, seed: int = 42) -> list[float]:
    rng = random.Random(seed)
    return [max(0.0, min(1.0, rng.gauss(mean, std))) for _ in range(n)]


@pytest.fixture
def scores_50() -> tuple[list[float], list[float]]:
    return _make_scores(50, 0.80), _make_scores(50, 0.72, seed=99)


@pytest.fixture
def scores_1000() -> tuple[list[float], list[float]]:
    return _make_scores(1000, 0.80), _make_scores(1000, 0.72, seed=99)


def test_mann_whitney_n50(benchmark: object, scores_50: tuple[list[float], list[float]]) -> None:
    a, b = scores_50
    result = benchmark(mann_whitney_u, a, b)  # type: ignore[operator]
    assert result.p_value < 1.0


def test_mann_whitney_n1000(benchmark: object, scores_1000: tuple[list[float], list[float]]) -> None:
    a, b = scores_1000
    result = benchmark(mann_whitney_u, a, b)  # type: ignore[operator]
    assert result.p_value < 1.0


def test_bootstrap_n1000(benchmark: object, scores_1000: tuple[list[float], list[float]]) -> None:
    a, b = scores_1000
    result = benchmark(bootstrap_mean_ci, a, b, 1000)  # type: ignore[operator]
    assert result.lower <= result.upper


def test_overhead_assertion_n1000(scores_1000: tuple[list[float], list[float]]) -> None:
    a, b = scores_1000
    start = time.perf_counter()
    mann_whitney_u(a, b)
    bootstrap_mean_ci(a, b, n_resamples=1000)
    compute_effect_sizes(a, b)
    elapsed_ms = (time.perf_counter() - start) * 1000
    assert elapsed_ms < 500, f"Statistical computation took {elapsed_ms:.1f}ms, expected < 500ms"
