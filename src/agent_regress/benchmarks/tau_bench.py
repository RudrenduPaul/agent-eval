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

    def _attempt(self, task: dict[str, Any]) -> bool:
        try:
            result = self.agent(task)
            score = float(result) if isinstance(result, (int, float)) else 0.0
            return score >= self.success_threshold
        except Exception as exc:
            warnings.warn(
                f"Agent raised exception on task: {exc}",
                UserWarning,
                stacklevel=2,
            )
            return False

    def _run_task_attempts(self, task: dict[str, Any], max_k: int) -> list[bool]:
        results: list[bool] = []
        for _ in range(max_k):
            success = self._attempt(task)
            results.append(success)
            if success:
                # any(results[:k]) == True for all k >= len(results) because
                # Python slicing past the end returns all elements.
                break
        return results

    def evaluate(self, k_values: list[int] | None = None) -> list[TauBenchResult]:
        if k_values is None:
            k_values = [1, 4, 8]
        if not self.dataset:
            raise ValueError("dataset must not be empty")

        max_k = max(k_values)
        # Run each task max_k times once; derive pass^k by checking first k attempts.
        per_task_attempts = [
            self._run_task_attempts(task, max_k) for task in self.dataset
        ]

        results: list[TauBenchResult] = []
        for k in sorted(k_values):
            task_passed = [any(attempts[:k]) for attempts in per_task_attempts]
            n_success = sum(task_passed)
            results.append(
                TauBenchResult(
                    k=k,
                    pass_at_k=n_success / len(self.dataset),
                    n_tasks=len(self.dataset),
                    n_successes=n_success,
                    task_scores=[1.0 if p else 0.0 for p in task_passed],
                )
            )
        return results
