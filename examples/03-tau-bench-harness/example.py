"""Example 03: Tau-bench pass^k harness.

Run with: python examples/03-tau-bench-harness/example.py
"""
from __future__ import annotations

import random
from typing import Any

from agent_regress.benchmarks.tau_bench import TauBenchHarness


def mock_agent(test_case: dict[str, Any]) -> float:
    rng = random.Random(hash(str(test_case)) % 10000)
    return 1.0 if rng.random() < 0.65 else 0.0


def main() -> None:
    dataset = [
        {"task_id": f"retail_task_{i}", "domain": "retail"}
        for i in range(50)
    ]

    harness = TauBenchHarness(agent=mock_agent, dataset=dataset)
    results = harness.evaluate(k_values=[1, 4, 8])

    print("Tau-bench pass^k results (mock agent, 65% single-attempt success):")
    print("-" * 55)
    for r in results:
        bar = "#" * int(r.pass_at_k * 40)
        print(f"  pass^{r.k}: {r.pass_at_k:.3f}  [{bar:<40}]")


if __name__ == "__main__":
    main()
