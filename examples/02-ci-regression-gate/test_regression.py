"""Example 02: CI regression gate for pytest.

Run with: pytest examples/02-ci-regression-gate/
"""

from __future__ import annotations

import random
from typing import Any

from agent_regress import compare


def _build_agent(base_score: float, noise: float = 0.05, seed: int = 0) -> Any:
    call_count = 0

    def _agent(test_case: dict[str, Any]) -> float:
        nonlocal call_count
        rng = random.Random(call_count + seed)
        call_count += 1
        return max(0.0, min(1.0, rng.gauss(base_score, noise)))

    return _agent


AGENT_V1 = _build_agent(base_score=0.82, seed=0)
AGENT_V2 = _build_agent(base_score=0.80, seed=999)

TEST_SUITE = [{"query": f"task_{i}", "expected": f"answer_{i}"} for i in range(10)]


def test_no_regression() -> None:
    report = compare(
        version_a=AGENT_V1,
        version_b=AGENT_V2,
        test_suite=TEST_SUITE,
        n_runs=50,
        metric="tool_accuracy",
    )
    print(report)
    report.assert_stable(p_threshold=0.05, min_effect=0.2)
