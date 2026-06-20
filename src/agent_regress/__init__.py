"""agent-regress: statistical regression testing for LLM agents.

Find out if your latest agent deploy made things worse -- statistically.

    from agent_regress import compare

    report = compare(
        version_a=my_agent_v1,
        version_b=my_agent_v2,
        test_suite=test_cases,
        n_runs=50,
    )
    print(report)
    report.assert_stable()
"""

from __future__ import annotations

from agent_regress.ci.gate import RegressionGate, assert_no_regression
from agent_regress.core.compare import compare
from agent_regress.core.report import Report, Verdict
from agent_regress.core.runner import run_suite
from agent_regress.core.scorer import exact_match_scorer, f1_scorer

__version__ = "0.1.0"
__all__ = [
    "RegressionGate",
    "Report",
    "Verdict",
    "__version__",
    "assert_no_regression",
    "compare",
    "exact_match_scorer",
    "f1_scorer",
    "run_suite",
]
