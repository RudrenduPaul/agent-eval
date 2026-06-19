"""SWE-bench Verified scaffold score harness.

Measures the framework contribution to SWE-bench pass rate independent
of the underlying model. A better scaffold (test runner, output parser,
verdict logic) can lift pass rates 5-15pp on the same model.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class SWEBenchResult:
    scaffold_pass_rate: float
    n_instances: int
    n_resolved: int
    instance_ids: list[str]
    resolved_ids: list[str]


@dataclass
class SWEBenchHarness:
    agent: Any
    dataset: list[dict[str, Any]]

    def _is_resolved(self, output: Any, instance: dict[str, Any]) -> bool:
        if isinstance(output, bool):
            return output
        if isinstance(output, (int, float)):
            return float(output) >= 0.5
        return str(output).strip().lower() in ("resolved", "true", "pass", "1")

    def evaluate(self) -> SWEBenchResult:
        if not self.dataset:
            raise ValueError("dataset must not be empty")

        resolved_ids: list[str] = []
        all_ids: list[str] = []

        for instance in self.dataset:
            instance_id = str(instance.get("instance_id", "unknown"))
            all_ids.append(instance_id)
            try:
                output = self.agent(instance)
                if self._is_resolved(output, instance):
                    resolved_ids.append(instance_id)
            except Exception:  # noqa: BLE001
                pass

        return SWEBenchResult(
            scaffold_pass_rate=len(resolved_ids) / len(self.dataset),
            n_instances=len(self.dataset),
            n_resolved=len(resolved_ids),
            instance_ids=all_ids,
            resolved_ids=resolved_ids,
        )
