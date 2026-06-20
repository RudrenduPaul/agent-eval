"""Tests for effect size calculations."""

from __future__ import annotations

import pytest

from agent_regress.stats.effect_size import (
    EffectSizeResult,
    cohens_d,
    compute_effect_sizes,
    interpret_cohens_d,
    rank_biserial_r,
)


class TestCohensD:
    def test_zero_for_identical(self) -> None:
        a = [0.8] * 30
        assert cohens_d(a, a) == 0.0

    def test_negative_when_b_lower(self) -> None:
        a = [0.8] * 50
        b = [0.6] * 50
        assert cohens_d(a, b) < 0.0

    def test_positive_when_b_higher(self) -> None:
        a = [0.6] * 50
        b = [0.8] * 50
        assert cohens_d(a, b) > 0.0

    def test_large_effect(self) -> None:
        a = [0.9] * 50
        b = [0.1] * 50
        d = cohens_d(a, b)
        assert abs(d) > 2.0

    def test_empty_a_raises(self) -> None:
        with pytest.raises(ValueError):
            cohens_d([], [0.5])

    def test_empty_b_raises(self) -> None:
        with pytest.raises(ValueError):
            cohens_d([0.5], [])

    def test_single_elements(self) -> None:
        d = cohens_d([0.8], [0.6])
        assert d == 0.0

    def test_inf_for_constant_arrays_with_different_means(self) -> None:
        # Both arrays constant but different — pooled std is 0, delta != 0.
        # Must return ±inf, not a huge spurious finite number from FP rounding
        # of near-zero variance on non-exactly-representable floats (0.8, 0.3…).
        assert cohens_d([0.8] * 50, [0.6] * 50) == float("-inf")
        assert cohens_d([0.3] * 50, [0.7] * 50) == float("inf")
        assert cohens_d([0.9] * 50, [0.1] * 50) == float("-inf")

    def test_known_value(self) -> None:
        import numpy as np

        rng = np.random.default_rng(42)
        a = list(rng.normal(0.8, 0.1, 100))
        b = list(rng.normal(0.7, 0.1, 100))
        d = cohens_d(a, b)
        assert abs(d) < 2.0
        assert d > 0.0 or d < 0.0  # just verify it is non-NaN


class TestRankBiserialR:
    def test_perfect_separation(self) -> None:
        a = [0.3] * 30
        b = [0.7] * 30
        r = rank_biserial_r(a, b)
        assert abs(r - 1.0) < 1e-9

    def test_empty_a_raises(self) -> None:
        with pytest.raises(ValueError):
            rank_biserial_r([], [0.5])

    def test_range(self) -> None:
        import random

        rng = random.Random(42)
        a = [rng.random() for _ in range(20)]
        b = [rng.random() for _ in range(20)]
        r = rank_biserial_r(a, b)
        assert -1.0 <= r <= 1.0


class TestInterpretCohensD:
    def test_negligible(self) -> None:
        assert interpret_cohens_d(0.1) == "negligible"

    def test_small(self) -> None:
        assert interpret_cohens_d(0.3) == "small"

    def test_medium(self) -> None:
        assert interpret_cohens_d(0.6) == "medium"

    def test_large(self) -> None:
        assert interpret_cohens_d(1.0) == "large"

    def test_negative(self) -> None:
        assert interpret_cohens_d(-0.3) == "small"


class TestComputeEffectSizes:
    def test_returns_all_fields(self) -> None:
        a = [0.8] * 30
        b = [0.6] * 30
        result = compute_effect_sizes(a, b)
        assert isinstance(result, EffectSizeResult)
        assert result.cohens_d < 0.0
        assert result.rank_biserial_r < 0.0
        assert result.interpretation in ("negligible", "small", "medium", "large")
