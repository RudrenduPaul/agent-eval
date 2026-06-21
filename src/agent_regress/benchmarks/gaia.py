"""GAIA Level 1-3 split harness.

GAIA (General AI Assistants benchmark) has three difficulty levels.
The Level 1-3 split reveals capability boundaries that aggregate scores hide.
"""

from __future__ import annotations

import warnings
from dataclasses import dataclass
from enum import IntEnum
from typing import Any


class GAIALevel(IntEnum):
    LEVEL_1 = 1
    LEVEL_2 = 2
    LEVEL_3 = 3


@dataclass(frozen=True)
class GAIALevelResult:
    level: GAIALevel
    accuracy: float
    n_questions: int
    n_correct: int


@dataclass
class GAIAHarness:
    agent: Any
    dataset: list[dict[str, Any]]

    def _is_correct(self, output: Any, task: dict[str, Any]) -> bool:
        if output is None:  # sentinel returned by _safe_run on exception
            return False
        expected = task.get("expected_answer", "")
        return str(output).strip().lower() == str(expected).strip().lower()

    def evaluate(self) -> list[GAIALevelResult]:
        if not self.dataset:
            raise ValueError("dataset must not be empty")

        by_level: dict[GAIALevel, list[dict[str, Any]]] = {lv: [] for lv in GAIALevel}
        for task in self.dataset:
            raw_level = task.get("level", 1)
            try:
                level = GAIALevel(int(raw_level))
            except (ValueError, TypeError):
                level = GAIALevel.LEVEL_1
            by_level[level].append(task)

        results: list[GAIALevelResult] = []
        for level, tasks in by_level.items():
            if not tasks:
                continue
            correct = sum(
                1 for task in tasks if self._is_correct(self._safe_run(task), task)
            )
            results.append(
                GAIALevelResult(
                    level=level,
                    accuracy=correct / len(tasks),
                    n_questions=len(tasks),
                    n_correct=correct,
                )
            )
        return sorted(results, key=lambda r: r.level)

    def _safe_run(self, task: dict[str, Any]) -> Any:
        try:
            return self.agent(task)
        except Exception as exc:
            task_id = task.get("task_id", task.get("question_id", "unknown"))
            warnings.warn(
                f"Agent raised exception on task {task_id}: {exc}",
                UserWarning,
                stacklevel=2,
            )
            return None
