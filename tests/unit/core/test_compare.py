"""Tests for the compare() primary public API."""

from __future__ import annotations

import warnings
from typing import Any

import pytest

from agent_regress import compare
from agent_regress.core.report import Verdict


def _fixed_agent(score: float) -> Any:
    def _agent(tc: dict[str, Any]) -> float:
        return score

    return _agent


SUITE_5 = [{"query": f"q{i}", "expected": f"a{i}"} for i in range(5)]
SUITE_3 = [{"query": f"q{i}", "expected": f"a{i}"} for i in range(3)]


class TestCompare:
    def test_stable_identical_agents(self) -> None:
        report = compare(
            version_a=_fixed_agent(0.8),
            version_b=_fixed_agent(0.8),
            test_suite=SUITE_5,
            n_runs=20,
            metric="performance",
        )
        assert report.verdict == Verdict.STABLE
        assert report.mean_a == pytest.approx(0.8)
        assert report.mean_b == pytest.approx(0.8)

    def test_regressed_verdict(self) -> None:
        report = compare(
            version_a=_fixed_agent(0.9),
            version_b=_fixed_agent(0.1),
            test_suite=SUITE_5,
            n_runs=30,
            metric="performance",
        )
        assert report.verdict == Verdict.REGRESSED
        assert report.effect_size < 0.0
        assert report.p_value < 0.001

    def test_improved_verdict(self) -> None:
        report = compare(
            version_a=_fixed_agent(0.1),
            version_b=_fixed_agent(0.9),
            test_suite=SUITE_5,
            n_runs=30,
            metric="performance",
        )
        assert report.verdict == Verdict.IMPROVED
        assert report.effect_size > 0.0

    def test_insufficient_data_verdict(self) -> None:
        # 3 cases * 3 runs = 9 scores total < 10 → INSUFFICIENT_DATA
        report = compare(
            version_a=_fixed_agent(0.8),
            version_b=_fixed_agent(0.5),
            test_suite=SUITE_3,
            n_runs=3,
            metric="performance",
        )
        assert report.verdict == Verdict.INSUFFICIENT_DATA

    def test_empty_test_suite_raises(self) -> None:
        with pytest.raises(ValueError, match="test_suite must not be empty"):
            compare(
                version_a=_fixed_agent(0.8),
                version_b=_fixed_agent(0.8),
                test_suite=[],
                n_runs=10,
                metric="performance",
            )

    def test_invalid_n_runs_raises(self) -> None:
        with pytest.raises(ValueError, match="n_runs must be >= 1"):
            compare(
                version_a=_fixed_agent(0.8),
                version_b=_fixed_agent(0.8),
                test_suite=SUITE_5,
                n_runs=0,
                metric="performance",
            )

    def test_invalid_p_threshold_raises(self) -> None:
        with pytest.raises(ValueError, match="p_threshold"):
            compare(
                version_a=_fixed_agent(0.8),
                version_b=_fixed_agent(0.8),
                test_suite=SUITE_5,
                p_threshold=1.5,
                metric="performance",
            )

    def test_negative_min_effect_raises(self) -> None:
        with pytest.raises(ValueError, match="min_effect"):
            compare(
                version_a=_fixed_agent(0.8),
                version_b=_fixed_agent(0.8),
                test_suite=SUITE_5,
                min_effect=-0.1,
                metric="performance",
            )

    def test_report_fields_present(self) -> None:
        report = compare(
            version_a=_fixed_agent(0.8),
            version_b=_fixed_agent(0.8),
            test_suite=SUITE_5,
            n_runs=15,
            metric="tool_accuracy",
        )
        assert report.metric == "tool_accuracy"
        assert 0.0 <= report.p_value <= 1.0
        assert report.n_a == 15 * 5
        assert report.n_b == 15 * 5
        assert report.ci_lower <= report.ci_upper

    def test_custom_scorer(self) -> None:
        def my_agent(tc: dict[str, Any]) -> str:
            return str(tc.get("expected", ""))

        def my_scorer(output: str, tc: dict[str, Any]) -> float:
            return 1.0 if output == str(tc.get("expected", "")) else 0.0

        report = compare(
            version_a=my_agent,
            version_b=my_agent,
            test_suite=SUITE_5,
            n_runs=15,
            scorer=my_scorer,
        )
        assert report.mean_a == pytest.approx(1.0)
        assert report.mean_b == pytest.approx(1.0)

    def test_warns_on_small_n(self) -> None:
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            compare(
                version_a=_fixed_agent(0.8),
                version_b=_fixed_agent(0.8),
                test_suite=SUITE_3,
                n_runs=5,
                metric="performance",
            )
        msgs = " ".join(str(warning.message) for warning in w)
        assert "insufficient" in msgs.lower() or "50" in msgs

    def test_default_exact_match_scorer_used(self) -> None:
        def perfect_agent(tc: dict[str, Any]) -> str:
            return str(tc.get("expected", ""))

        report = compare(
            version_a=perfect_agent,
            version_b=perfect_agent,
            test_suite=SUITE_5,
            n_runs=10,
            metric="accuracy",
        )
        assert report.mean_a == pytest.approx(1.0)
        assert report.mean_b == pytest.approx(1.0)

    def test_assert_stable_does_not_raise_on_stable(self) -> None:
        report = compare(
            version_a=_fixed_agent(0.8),
            version_b=_fixed_agent(0.8),
            test_suite=SUITE_5,
            n_runs=20,
            metric="performance",
        )
        report.assert_stable()

    def test_assert_stable_raises_on_regression(self) -> None:
        report = compare(
            version_a=_fixed_agent(0.9),
            version_b=_fixed_agent(0.1),
            test_suite=SUITE_5,
            n_runs=30,
            metric="performance",
        )
        with pytest.raises(AssertionError, match="REGRESSED"):
            report.assert_stable()
