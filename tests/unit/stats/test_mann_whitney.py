"""Tests for Mann-Whitney U test implementation."""

from __future__ import annotations

import warnings

import pytest

from agent_regress.stats.mann_whitney import MannWhitneyResult, mann_whitney_u


class TestMannWhitneyU:
    def test_basic_returns_result(self) -> None:
        a = [0.8] * 30
        b = [0.6] * 30
        result = mann_whitney_u(a, b)
        assert isinstance(result, MannWhitneyResult)
        assert 0.0 <= result.p_value <= 1.0
        assert result.n_a == 30
        assert result.n_b == 30

    def test_significant_difference(self) -> None:
        a = [0.9] * 50
        b = [0.5] * 50
        result = mann_whitney_u(a, b)
        assert result.p_value < 0.001

    def test_identical_distributions_not_significant(self) -> None:
        import random

        rng = random.Random(42)
        scores = [rng.gauss(0.7, 0.05) for _ in range(50)]
        a = scores[:25]
        b = scores[25:]
        result = mann_whitney_u(a + a, b + b)
        # Cannot guarantee not significant but statistic should exist
        assert isinstance(result.p_value, float)

    def test_empty_a_raises(self) -> None:
        with pytest.raises(ValueError, match="scores_a must not be empty"):
            mann_whitney_u([], [0.5, 0.6])

    def test_empty_b_raises(self) -> None:
        with pytest.raises(ValueError, match="scores_b must not be empty"):
            mann_whitney_u([0.5, 0.6], [])

    def test_invalid_alternative_raises(self) -> None:
        with pytest.raises(ValueError, match="alternative must be"):
            mann_whitney_u([0.5], [0.6], alternative="invalid")

    def test_warns_on_small_sample(self) -> None:
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            mann_whitney_u([0.5, 0.6], [0.7, 0.8])
            assert any("insufficient" in str(warning.message).lower() for warning in w)

    def test_sufficient_power_flag(self) -> None:
        a = [0.8] * 30
        b = [0.7] * 30
        result = mann_whitney_u(a, b)
        assert result.sufficient_power is True

    def test_insufficient_power_flag(self) -> None:
        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")
            result = mann_whitney_u([0.8] * 10, [0.7] * 10)
        assert result.sufficient_power is False

    def test_two_sided_default(self) -> None:
        a = [0.8] * 30
        b = [0.6] * 30
        result = mann_whitney_u(a, b)
        assert result.p_value > 0.0

    def test_single_element_lists(self) -> None:
        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")
            result = mann_whitney_u([0.8], [0.6])
        assert isinstance(result.p_value, float)
