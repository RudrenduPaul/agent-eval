"""Tests for run_suite."""
from __future__ import annotations

import warnings
from typing import Any

import pytest

from agent_regress.core.runner import run_suite


def _fixed_agent(score: float) -> Any:
    def _agent(test_case: dict[str, Any]) -> float:
        return score
    return _agent


class TestRunSuite:
    def test_basic_run(self, basic_test_suite: list[dict[str, Any]]) -> None:
        scores = run_suite(_fixed_agent(0.8), basic_test_suite, n_runs=3)
        assert len(scores) == 5 * 3
        assert all(s == 0.8 for s in scores)

    def test_returns_floats(self, basic_test_suite: list[dict[str, Any]]) -> None:
        scores = run_suite(_fixed_agent(1), basic_test_suite, n_runs=2)
        assert all(isinstance(s, float) for s in scores)

    def test_empty_test_suite_raises(self) -> None:
        with pytest.raises(ValueError, match="test_suite must not be empty"):
            run_suite(_fixed_agent(0.8), [], n_runs=5)

    def test_zero_runs_raises(self, basic_test_suite: list[dict[str, Any]]) -> None:
        with pytest.raises(ValueError, match="n_runs must be >= 1"):
            run_suite(_fixed_agent(0.8), basic_test_suite, n_runs=0)

    def test_non_callable_raises(self, basic_test_suite: list[dict[str, Any]]) -> None:
        with pytest.raises(TypeError, match="agent must be callable"):
            run_suite("not_callable", basic_test_suite, n_runs=2)  # type: ignore[arg-type]

    def test_warns_on_low_n_runs(self, basic_test_suite: list[dict[str, Any]]) -> None:
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            run_suite(_fixed_agent(0.8), basic_test_suite, n_runs=3)
            assert any(issubclass(warning.category, UserWarning) for warning in w)

    def test_custom_scorer(self, basic_test_suite: list[dict[str, Any]]) -> None:
        def _agent(tc: dict[str, Any]) -> str:
            return "answer"

        def _scorer(output: Any, tc: dict[str, Any]) -> float:
            return 0.9

        scores = run_suite(_agent, basic_test_suite, n_runs=2, scorer=_scorer)
        assert all(s == 0.9 for s in scores)

    def test_non_float_output_without_scorer_raises(
        self, basic_test_suite: list[dict[str, Any]]
    ) -> None:
        def _str_agent(tc: dict[str, Any]) -> str:
            return "some text"

        with pytest.raises(TypeError, match="scorer="):
            run_suite(_str_agent, basic_test_suite, n_runs=2)

    def test_score_clamping_warns(self, basic_test_suite: list[dict[str, Any]]) -> None:
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            run_suite(_fixed_agent(1.5), basic_test_suite, n_runs=2)
            assert any("Clamping" in str(warning.message) for warning in w)
