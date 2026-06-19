"""Example 04: Model upgrade audit (GPT-4o vs GPT-4o-mini).

Run with: python examples/04-model-upgrade-audit/example.py
"""

from __future__ import annotations

import random
from typing import Any

from agent_regress import compare


def gpt4o_agent(test_case: dict[str, Any]) -> str:
    rng = random.Random(hash(str(test_case)) % 10000)
    return str(test_case.get("expected", "")) if rng.random() < 0.85 else "incorrect"


def gpt4o_mini_agent(test_case: dict[str, Any]) -> str:
    rng = random.Random(hash(str(test_case)) % 10000 + 777)
    return str(test_case.get("expected", "")) if rng.random() < 0.72 else "incorrect"


def exact_match(output: str, test_case: dict[str, Any]) -> float:
    return 1.0 if output.strip() == str(test_case.get("expected", "")).strip() else 0.0


def main() -> None:
    test_suite = [{"query": f"q_{i}", "expected": f"answer_{i}"} for i in range(15)]

    report = compare(
        version_a=gpt4o_agent,
        version_b=gpt4o_mini_agent,
        test_suite=test_suite,
        n_runs=50,
        metric="exact_match_accuracy",
        scorer=exact_match,
    )
    print(report)


if __name__ == "__main__":
    main()
