"""Tests for the CI regression gate."""

from __future__ import annotations

import warnings

import pytest

from agent_regress.ci.gate import RegressionGate, assert_no_regression
from agent_regress.core.report import Report, Verdict


def _make_report(
    verdict: Verdict = Verdict.STABLE,
    p_value: float = 0.41,
    effect_size: float = 0.05,
    n_a: int = 50,
    n_b: int = 50,
    mean_a: float = 0.80,
    mean_b: float = 0.80,
) -> Report:
    return Report(
        metric="accuracy",
        verdict=verdict,
        p_value=p_value,
        effect_size=effect_size,
        ci_lower=-0.02,
        ci_upper=0.03,
        n_a=n_a,
        n_b=n_b,
        mean_a=mean_a,
        mean_b=mean_b,
        std_a=0.05,
        std_b=0.05,
        mean_delta=mean_b - mean_a,
        warnings=[],
    )


class TestAssertNoRegression:
    def test_stable_passes(self) -> None:
        assert_no_regression(_make_report(verdict=Verdict.STABLE))

    def test_improved_passes(self) -> None:
        assert_no_regression(_make_report(verdict=Verdict.IMPROVED))

    def test_regressed_raises(self) -> None:
        report = _make_report(
            verdict=Verdict.REGRESSED,
            p_value=0.003,
            effect_size=-0.61,
            mean_a=0.84,
            mean_b=0.70,
        )
        with pytest.raises(AssertionError, match="REGRESSED"):
            assert_no_regression(report)

    def test_insufficient_data_warns_not_fails(self) -> None:
        report = _make_report(verdict=Verdict.REGRESSED, n_a=5, n_b=5)
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            assert_no_regression(report)
        assert any(issubclass(warning.category, UserWarning) for warning in w)

    def test_small_sample_does_not_raise(self) -> None:
        report = _make_report(verdict=Verdict.REGRESSED, n_a=10, n_b=10)
        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")
            assert_no_regression(report)

    def test_custom_threshold(self) -> None:
        report = _make_report(
            verdict=Verdict.REGRESSED,
            p_value=0.06,
            effect_size=-0.3,
            mean_a=0.84,
            mean_b=0.78,
        )
        # With a stricter threshold, should pass
        assert_no_regression(report, p_threshold=0.01)

    def test_gate_uses_own_thresholds_not_verdict(self) -> None:
        # Report was computed with strict thresholds (p_threshold=0.01) so
        # verdict=STABLE even though p=0.03 is significant at p=0.05.
        # The gate must re-evaluate with its own threshold, not trust verdict.
        report = _make_report(
            verdict=Verdict.STABLE,
            p_value=0.03,
            effect_size=-0.35,
            mean_a=0.84,
            mean_b=0.78,
        )
        with pytest.raises(AssertionError, match="REGRESSED"):
            assert_no_regression(report, p_threshold=0.05)


class TestRegressionGate:
    def test_default_thresholds(self) -> None:
        gate = RegressionGate()
        assert gate.p_threshold == 0.05
        assert gate.min_effect == 0.2

    def test_custom_thresholds(self) -> None:
        gate = RegressionGate(p_threshold=0.01, min_effect=0.5)
        assert gate.p_threshold == 0.01
        assert gate.min_effect == 0.5

    def test_invalid_p_threshold_raises(self) -> None:
        with pytest.raises(ValueError, match="p_threshold"):
            RegressionGate(p_threshold=1.5)

    def test_invalid_min_effect_raises(self) -> None:
        with pytest.raises(ValueError, match="min_effect"):
            RegressionGate(min_effect=-0.1)

    def test_check_stable_passes(self) -> None:
        gate = RegressionGate()
        gate.check(_make_report(verdict=Verdict.STABLE))

    def test_check_regressed_raises(self) -> None:
        gate = RegressionGate()
        report = _make_report(
            verdict=Verdict.REGRESSED,
            p_value=0.003,
            effect_size=-0.61,
            mean_a=0.84,
            mean_b=0.70,
        )
        with pytest.raises(AssertionError):
            gate.check(report)

    def test_repr(self) -> None:
        gate = RegressionGate(p_threshold=0.05, min_effect=0.2)
        assert "RegressionGate" in repr(gate)
        assert "0.05" in repr(gate)
