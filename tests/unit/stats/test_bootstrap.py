"""Tests for bootstrap confidence interval implementation."""
from __future__ import annotations

import pytest

from agent_regress.stats.bootstrap import bootstrap_mean_ci, BootstrapCI


class TestBootstrapMeanCI:
    def test_basic_returns_ci(
        self, sample_scores_a: list[float], sample_scores_b: list[float]
    ) -> None:
        ci = bootstrap_mean_ci(sample_scores_a, sample_scores_b, n_resamples=200)
        assert isinstance(ci, BootstrapCI)
        assert ci.lower <= ci.upper
        assert ci.n_resamples == 200
        assert ci.confidence == 0.95

    def test_negative_delta_on_regression(
        self, sample_scores_a: list[float], sample_scores_b: list[float]
    ) -> None:
        ci = bootstrap_mean_ci(sample_scores_a, sample_scores_b, n_resamples=200)
        assert ci.mean_delta < 0.0

    def test_ci_contains_zero_for_similar(self) -> None:
        a = [0.75] * 50
        b = [0.76] * 50
        ci = bootstrap_mean_ci(a, b, n_resamples=200)
        assert ci.lower <= 0.0 <= ci.upper

    def test_empty_a_raises(self) -> None:
        with pytest.raises(ValueError, match="scores_a must not be empty"):
            bootstrap_mean_ci([], [0.5])

    def test_empty_b_raises(self) -> None:
        with pytest.raises(ValueError, match="scores_b must not be empty"):
            bootstrap_mean_ci([0.5], [])

    def test_too_few_resamples_raises(self) -> None:
        with pytest.raises(ValueError, match="n_resamples must be >= 100"):
            bootstrap_mean_ci([0.5] * 10, [0.6] * 10, n_resamples=50)

    def test_invalid_confidence_raises(self) -> None:
        with pytest.raises(ValueError, match="confidence must be in"):
            bootstrap_mean_ci([0.5] * 10, [0.6] * 10, confidence=1.5)

    def test_reproducible_with_seed(self) -> None:
        a = [0.8] * 30
        b = [0.7] * 30
        ci1 = bootstrap_mean_ci(a, b, n_resamples=200, seed=7)
        ci2 = bootstrap_mean_ci(a, b, n_resamples=200, seed=7)
        assert ci1.lower == ci2.lower
        assert ci1.upper == ci2.upper

    def test_different_seeds_may_differ(self) -> None:
        a = [0.8] * 30
        b = [0.7] * 30
        ci1 = bootstrap_mean_ci(a, b, n_resamples=500, seed=1)
        ci2 = bootstrap_mean_ci(a, b, n_resamples=500, seed=2)
        # Results should be close but not necessarily identical
        assert abs(ci1.mean_delta - ci2.mean_delta) < 0.001

    def test_mean_delta_equals_mean_difference(self) -> None:
        a = [0.8] * 50
        b = [0.6] * 50
        ci = bootstrap_mean_ci(a, b, n_resamples=200)
        assert abs(ci.mean_delta - (-0.2)) < 1e-9
