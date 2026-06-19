"""Benchmark: SWE-bench scaffold score demonstration.

Run: uv run pytest benchmarks/test_swebench.py -v
"""
from __future__ import annotations

import random
from typing import Any

import pytest

from agent_regress.benchmarks.swebench import SWEBenchHarness


def _mock_agent(resolve_rate: float = 0.30) -> Any:
    call_count = 0

    def _agent(instance: dict[str, Any]) -> bool:
        nonlocal call_count
        rng = random.Random(call_count)
        call_count += 1
        return rng.random() < resolve_rate

    return _agent


MOCK_INSTANCES = [
    {"instance_id": f"repo__issue_{i}", "repo": "mock/repo"}
    for i in range(100)
]


def test_swebench_scaffold_score() -> None:
    agent = _mock_agent(resolve_rate=0.30)
    harness = SWEBenchHarness(agent=agent, dataset=MOCK_INSTANCES)
    result = harness.evaluate()

    print(f"\nSWE-bench scaffold score: {result.scaffold_pass_rate:.3f}")
    print(f"Resolved: {result.n_resolved}/{result.n_instances}")

    assert 0.0 <= result.scaffold_pass_rate <= 1.0
    assert result.n_instances == 100
