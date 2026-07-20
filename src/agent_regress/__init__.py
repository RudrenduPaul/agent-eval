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

from importlib.metadata import PackageNotFoundError, version

from agent_regress.ci.gate import RegressionGate, assert_no_regression
from agent_regress.core.compare import compare
from agent_regress.core.report import Report, Verdict
from agent_regress.core.runner import (
    AgentCallable,
    AsyncAgentCallable,
    ScorerCallable,
    arun_suite,
    concurrent_cancellation_probe,
    run_suite,
    subprocess_runner,
)
from agent_regress.core.scorer import (
    exact_match_scorer,
    f1_scorer,
    no_path_leak_scorer,
    schema_conformance_scorer,
    state_diff_scorer,
    structured_content_scorer,
    tool_call_trace_scorer,
)

try:
    __version__ = version("agent-regress-cli")
except PackageNotFoundError:
    # Editable/source checkout with no installed dist-info (e.g. running
    # straight from a git clone without `pip install -e .`).
    __version__ = "0.0.0+unknown"
__all__ = [
    "AgentCallable",
    "AsyncAgentCallable",
    "RegressionGate",
    "Report",
    "ScorerCallable",
    "Verdict",
    "__version__",
    "arun_suite",
    "assert_no_regression",
    "compare",
    "concurrent_cancellation_probe",
    "exact_match_scorer",
    "f1_scorer",
    "no_path_leak_scorer",
    "run_suite",
    "schema_conformance_scorer",
    "state_diff_scorer",
    "structured_content_scorer",
    "subprocess_runner",
    "tool_call_trace_scorer",
]
