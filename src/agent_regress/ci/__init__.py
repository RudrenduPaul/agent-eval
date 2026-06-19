"""CI gate for blocking deploys on statistically significant regressions."""

from agent_regress.ci.gate import RegressionGate, assert_no_regression

__all__ = ["RegressionGate", "assert_no_regression"]
