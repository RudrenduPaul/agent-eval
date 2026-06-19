"""CI gate: raises AssertionError on statistically significant regression.

Designed for use as a pytest test step. Import and call assert_no_regression()
or use RegressionGate.check() inside a test function.
"""

from __future__ import annotations

import warnings

from agent_regress.core.report import Report, Verdict

_MIN_N_WARNING = 30


def assert_no_regression(
    report: Report,
    p_threshold: float = 0.05,
    min_effect: float = 0.2,
) -> None:
    if report.n_a < _MIN_N_WARNING or report.n_b < _MIN_N_WARNING:
        warnings.warn(
            f"n_a={report.n_a}, n_b={report.n_b}: insufficient sample size for "
            "reliable regression detection. Not failing the build due to "
            "insufficient data. Use at least 30 runs per version.",
            UserWarning,
            stacklevel=2,
        )
        return

    if report.verdict == Verdict.REGRESSED:
        report.assert_stable(p_threshold=p_threshold, min_effect=min_effect)


class RegressionGate:
    def __init__(
        self,
        p_threshold: float = 0.05,
        min_effect: float = 0.2,
    ) -> None:
        if not (0.0 < p_threshold < 1.0):
            raise ValueError(f"p_threshold must be in (0, 1), got {p_threshold}")
        if min_effect < 0.0:
            raise ValueError(f"min_effect must be >= 0, got {min_effect}")
        self.p_threshold = p_threshold
        self.min_effect = min_effect

    def check(self, report: Report) -> None:
        assert_no_regression(
            report,
            p_threshold=self.p_threshold,
            min_effect=self.min_effect,
        )

    def __repr__(self) -> str:
        return (
            f"RegressionGate(p_threshold={self.p_threshold}, "
            f"min_effect={self.min_effect})"
        )
