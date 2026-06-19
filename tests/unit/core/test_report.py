"""Tests for Report dataclass and Verdict enum."""
from __future__ import annotations

import pytest

from agent_regress.core.report import Report, Verdict


def _make_report(**kwargs: object) -> Report:
    defaults: dict[str, object] = dict(
        metric="accuracy",
        verdict=Verdict.STABLE,
        p_value=0.41,
        effect_size=0.05,
        ci_lower=-0.02,
        ci_upper=0.03,
        n_a=50,
        n_b=50,
        mean_a=0.80,
        mean_b=0.81,
        std_a=0.05,
        std_b=0.05,
        mean_delta=0.01,
        warnings=[],
    )
    defaults.update(kwargs)  # type: ignore[arg-type]
    return Report(**defaults)  # type: ignore[arg-type]


class TestVerdict:
    def test_all_values(self) -> None:
        assert Verdict.REGRESSED == "REGRESSED"
        assert Verdict.STABLE == "STABLE"
        assert Verdict.IMPROVED == "IMPROVED"
        assert Verdict.INSUFFICIENT_DATA == "INSUFFICIENT_DATA"


class TestReport:
    def test_stable_does_not_raise(self) -> None:
        report = _make_report(verdict=Verdict.STABLE)
        report.assert_stable()

    def test_regressed_raises_assertion_error(self) -> None:
        report = _make_report(
            verdict=Verdict.REGRESSED,
            p_value=0.003,
            effect_size=-0.61,
            ci_lower=-0.22,
            ci_upper=-0.07,
            mean_a=0.84,
            mean_b=0.70,
            mean_delta=-0.14,
        )
        with pytest.raises(AssertionError, match="REGRESSED"):
            report.assert_stable()

    def test_improved_does_not_raise(self) -> None:
        report = _make_report(verdict=Verdict.IMPROVED)
        report.assert_stable()

    def test_insufficient_data_does_not_raise(self) -> None:
        report = _make_report(verdict=Verdict.INSUFFICIENT_DATA)
        report.assert_stable()

    def test_str_contains_verdict(self) -> None:
        report = _make_report()
        assert "STABLE" in str(report)

    def test_str_contains_metric(self) -> None:
        report = _make_report(metric="tool_accuracy")
        assert "tool_accuracy" in str(report)

    def test_str_contains_p_value(self) -> None:
        report = _make_report(p_value=0.0234)
        assert "0.0234" in str(report)

    def test_warnings_in_str(self) -> None:
        report = _make_report(warnings=["insufficient sample size"])
        assert "insufficient sample size" in str(report)

    def test_immutable(self) -> None:
        report = _make_report()
        with pytest.raises(Exception):
            report.verdict = Verdict.REGRESSED  # type: ignore[misc]
