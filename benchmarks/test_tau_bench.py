"""Benchmark: Tau-bench pass^k harness demonstration.

Run: uv run pytest benchmarks/test_tau_bench.py -v
"""

from __future__ import annotations

import random
from typing import Any

from agent_regress.benchmarks.tau_bench import TauBenchHarness, TauBenchResult


def _mock_agent(success_rate: float = 0.60, seed: int = 42) -> Any:
    call_count = 0

    def _agent(task: dict[str, Any]) -> float:
        nonlocal call_count
        rng = random.Random(call_count + seed)
        call_count += 1
        return 1.0 if rng.random() < success_rate else 0.0

    return _agent


MOCK_DATASET = [{"task_id": f"task_{i}", "domain": "retail"} for i in range(50)]


def test_tau_bench_pass_k_degradation() -> None:
    agent = _mock_agent(success_rate=0.60)
    harness = TauBenchHarness(agent=agent, dataset=MOCK_DATASET)
    results = harness.evaluate(k_values=[1, 4, 8])

    assert len(results) == 3
    k1 = next(r for r in results if r.k == 1)
    k8 = next(r for r in results if r.k == 8)

    print("\nTau-bench pass^k (mock agent, p_success=0.60):")
    for r in results:
        print(f"  pass^{r.k}: {r.pass_at_k:.3f}  ({r.n_successes}/{r.n_tasks} tasks)")

    assert k8.pass_at_k >= k1.pass_at_k


def test_tau_bench_result_structure() -> None:
    agent = _mock_agent(success_rate=0.80)
    harness = TauBenchHarness(agent=agent, dataset=MOCK_DATASET[:10])
    results = harness.evaluate(k_values=[1])
    result = results[0]
    assert isinstance(result, TauBenchResult)
    assert result.k == 1
    assert 0.0 <= result.pass_at_k <= 1.0
