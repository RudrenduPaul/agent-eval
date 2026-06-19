"""Example 01: Basic comparison between two agent versions.

Run with: python examples/01-basic-comparison/example.py
"""

from __future__ import annotations

import random
from typing import Any

from agent_regress import compare


def agent_v1(test_case: dict[str, Any]) -> float:
    rng = random.Random(hash(str(test_case)) % 10000)
    return max(0.0, min(1.0, rng.gauss(0.82, 0.05)))


def agent_v2(test_case: dict[str, Any]) -> float:
    rng = random.Random(hash(str(test_case)) % 10000 + 500)
    return max(0.0, min(1.0, rng.gauss(0.68, 0.08)))


def main() -> None:
    test_suite = [
        {"query": f"find SKU for order {1000 + i}", "expected": f"SKU-{4000 + i}"}
        for i in range(10)
    ]

    print("Running 50 trials of each agent version on 10 test cases...\n")

    report = compare(
        version_a=agent_v1,
        version_b=agent_v2,
        test_suite=test_suite,
        n_runs=50,
        metric="tool_accuracy",
    )

    print(report)


if __name__ == "__main__":
    main()
