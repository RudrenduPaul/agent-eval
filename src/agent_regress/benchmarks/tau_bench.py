"""Tau-bench pass^k harness.

pass^k measures the probability that an agent succeeds on at least one
attempt out of k independent runs. This captures reliability degradation
that single-run benchmarks hide: an agent that succeeds 60% of the time
will have pass^1=0.60, pass^4=0.974, pass^8=0.9993.

Usage:
    harness = TauBenchHarness(agent=my_agent, dataset=load_tau_bench())
    result = harness.evaluate(k_values=[1, 4, 8])
"""
from __future__ import annotations

import warnings
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class TauBenchResult:
    k: int
    pass_at_k: float
    n_tasks: int
    n_successes: int
    task_scores: list[float]


@dataclass
class TauBenchHarness:
    agent: Any
    dataset: list[dict[str, Any]]
    success_threshold: float = 0.5

    def _run_task_k_times(self, task: dict[str, Any], k: int) -> bool:
        for _ in range(k):
            try:
                result = self.agent(task)
                score = float(result) if isinstance(result, (int, float)) else 0.0
                if score >= self.success_threshold:
                    return True
            except Exception as exc:  # noqa: BLE001
                warnings.warn(f"Agent raised exception on task: {exc}", UserWarning, stacklevel=3)
        return False

    def evaluate(self, k_values: list[int] | None = None) -> list[TauBenchResult]:
        if k_values is None:
            k_values = [1, 4, 8]
        if not self.dataset:
            raise ValueError("dataset must not be empty")

        results: list[TauBenchResult] = []
        for k in k_values:
            task_results = [self._run_task_k_times(task, k) for task in self.dataset]
            n_success = sum(task_results)
            task_scores = [1.0 if r else 0.0 for r in task_results]
            results.append(
                TauBenchResult(
                    k=k,
                    pass_at_k=n_success / len(self.dataset),
                    n_tasks=len(self.dataset),
                    n_successes=n_success,
                    task_scores=task_scores,
                )
            )
        return results
