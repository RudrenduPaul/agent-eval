"""Benchmark: GAIA Level 1-3 split harness demonstration.

Run: uv run pytest benchmarks/test_gaia.py -v
"""

from __future__ import annotations

import random
from typing import Any

from agent_regress.benchmarks.gaia import GAIAHarness, GAIALevel


def _mock_agent(level_accuracy: dict[int, float] | None = None) -> Any:
    if level_accuracy is None:
        level_accuracy = {1: 0.85, 2: 0.55, 3: 0.25}
    call_count = 0

    def _agent(task: dict[str, Any]) -> str:
        nonlocal call_count
        level = int(task.get("level", 1))
        accuracy = level_accuracy.get(level, 0.5)  # type: ignore[union-attr]
        rng = random.Random(call_count)
        call_count += 1
        expected = task.get("expected_answer", "")
        return str(expected) if rng.random() < accuracy else "wrong answer"

    return _agent


MOCK_DATASET = (
    [
        {"question_id": f"L1_{i}", "level": 1, "expected_answer": f"ans_{i}"}
        for i in range(40)
    ]
    + [
        {"question_id": f"L2_{i}", "level": 2, "expected_answer": f"ans_{i}"}
        for i in range(30)
    ]
    + [
        {"question_id": f"L3_{i}", "level": 3, "expected_answer": f"ans_{i}"}
        for i in range(30)
    ]
)


def test_gaia_level_split() -> None:
    agent = _mock_agent()
    harness = GAIAHarness(agent=agent, dataset=MOCK_DATASET)
    results = harness.evaluate()

    print("\nGAIA Level 1-3 split (mock agent):")
    for r in results:
        print(f"  Level {r.level}: {r.accuracy:.3f}  ({r.n_correct}/{r.n_questions})")

    levels = [r.level for r in results]
    assert GAIALevel.LEVEL_1 in levels
