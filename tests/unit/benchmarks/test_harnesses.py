"""Unit tests for src/agent_regress/benchmarks/ harnesses."""

from __future__ import annotations

from typing import Any

import pytest

from agent_regress.benchmarks.gaia import GAIAHarness, GAIALevel, GAIALevelResult
from agent_regress.benchmarks.swebench import SWEBenchHarness, SWEBenchResult
from agent_regress.benchmarks.tau_bench import TauBenchHarness, TauBenchResult


def _always_succeed(tc: dict[str, Any]) -> float:
    return 1.0


def _always_fail(tc: dict[str, Any]) -> float:
    return 0.0


MINI_DATASET = [{"task_id": f"t{i}", "domain": "retail"} for i in range(5)]

GAIA_DATASET = (
    [
        {"question_id": f"L1_{i}", "level": 1, "expected_answer": f"ans_{i}"}
        for i in range(4)
    ]
    + [
        {"question_id": f"L2_{i}", "level": 2, "expected_answer": f"ans_{i}"}
        for i in range(3)
    ]
    + [
        {"question_id": f"L3_{i}", "level": 3, "expected_answer": f"ans_{i}"}
        for i in range(3)
    ]
)

SWE_DATASET = [{"instance_id": f"repo__issue_{i}"} for i in range(5)]


class TestTauBenchHarness:
    def test_perfect_agent_passes_all(self) -> None:
        harness = TauBenchHarness(agent=_always_succeed, dataset=MINI_DATASET)
        results = harness.evaluate(k_values=[1])
        assert len(results) == 1
        assert results[0].pass_at_k == 1.0
        assert results[0].n_successes == 5

    def test_failing_agent_passes_none(self) -> None:
        harness = TauBenchHarness(agent=_always_fail, dataset=MINI_DATASET)
        results = harness.evaluate(k_values=[1, 4])
        assert all(r.pass_at_k == 0.0 for r in results)

    def test_default_k_values(self) -> None:
        harness = TauBenchHarness(agent=_always_succeed, dataset=MINI_DATASET)
        results = harness.evaluate()
        ks = [r.k for r in results]
        assert ks == [1, 4, 8]

    def test_empty_dataset_raises(self) -> None:
        harness = TauBenchHarness(agent=_always_succeed, dataset=[])
        with pytest.raises(ValueError, match="dataset must not be empty"):
            harness.evaluate()

    def test_result_structure(self) -> None:
        harness = TauBenchHarness(agent=_always_succeed, dataset=MINI_DATASET)
        result = harness.evaluate(k_values=[1])[0]
        assert isinstance(result, TauBenchResult)
        assert result.k == 1
        assert result.n_tasks == 5
        assert len(result.task_scores) == 5

    def test_agent_exception_treated_as_failure(self) -> None:
        def _raise_agent(tc: dict[str, Any]) -> float:
            raise RuntimeError("agent crashed")

        import warnings

        harness = TauBenchHarness(agent=_raise_agent, dataset=MINI_DATASET)
        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")
            results = harness.evaluate(k_values=[1])
        assert results[0].pass_at_k == 0.0

    def test_pass_at_k_increases_with_k(self) -> None:
        import random

        call_count = 0

        def _prob_agent(tc: dict[str, Any]) -> float:
            nonlocal call_count
            rng = random.Random(call_count)
            call_count += 1
            return 1.0 if rng.random() < 0.6 else 0.0

        harness = TauBenchHarness(agent=_prob_agent, dataset=MINI_DATASET * 4)
        results = harness.evaluate(k_values=[1, 4, 8])
        k1 = next(r for r in results if r.k == 1)
        k8 = next(r for r in results if r.k == 8)
        assert k8.pass_at_k >= k1.pass_at_k


class TestGAIAHarness:
    def test_correct_agent_scores_100(self) -> None:
        def _correct_agent(tc: dict[str, Any]) -> str:
            return str(tc.get("expected_answer", ""))

        harness = GAIAHarness(agent=_correct_agent, dataset=GAIA_DATASET)
        results = harness.evaluate()
        for r in results:
            assert r.accuracy == pytest.approx(1.0)

    def test_wrong_agent_scores_0(self) -> None:
        def _wrong_agent(tc: dict[str, Any]) -> str:
            return "definitely wrong"

        harness = GAIAHarness(agent=_wrong_agent, dataset=GAIA_DATASET)
        results = harness.evaluate()
        for r in results:
            assert r.accuracy == pytest.approx(0.0)

    def test_levels_split_correctly(self) -> None:
        def _correct_agent(tc: dict[str, Any]) -> str:
            return str(tc.get("expected_answer", ""))

        harness = GAIAHarness(agent=_correct_agent, dataset=GAIA_DATASET)
        results = harness.evaluate()
        levels = [r.level for r in results]
        assert GAIALevel.LEVEL_1 in levels
        assert GAIALevel.LEVEL_2 in levels
        assert GAIALevel.LEVEL_3 in levels

    def test_results_sorted_by_level(self) -> None:
        def _correct_agent(tc: dict[str, Any]) -> str:
            return str(tc.get("expected_answer", ""))

        harness = GAIAHarness(agent=_correct_agent, dataset=GAIA_DATASET)
        results = harness.evaluate()
        assert results[0].level < results[1].level

    def test_empty_dataset_raises(self) -> None:
        harness = GAIAHarness(agent=_always_succeed, dataset=[])
        with pytest.raises(ValueError, match="dataset must not be empty"):
            harness.evaluate()

    def test_result_structure(self) -> None:
        def _correct_agent(tc: dict[str, Any]) -> str:
            return str(tc.get("expected_answer", ""))

        harness = GAIAHarness(agent=_correct_agent, dataset=GAIA_DATASET)
        result = harness.evaluate()[0]
        assert isinstance(result, GAIALevelResult)
        assert result.n_correct <= result.n_questions

    def test_invalid_level_defaults_to_level1(self) -> None:
        dataset = [{"question_id": "x", "level": 99, "expected_answer": "a"}]

        def _correct_agent(tc: dict[str, Any]) -> str:
            return "a"

        harness = GAIAHarness(agent=_correct_agent, dataset=dataset)
        results = harness.evaluate()
        assert any(r.level == GAIALevel.LEVEL_1 for r in results)

    def test_agent_exception_warns_and_scores_zero(self) -> None:
        import warnings

        def _raise_agent(tc: dict[str, Any]) -> str:
            raise RuntimeError("gaia agent crashed")

        harness = GAIAHarness(agent=_raise_agent, dataset=GAIA_DATASET)
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            results = harness.evaluate()
        assert any(issubclass(warning.category, UserWarning) for warning in w)
        for r in results:
            assert r.accuracy == pytest.approx(0.0)


class TestSWEBenchHarness:
    def test_resolved_agent(self) -> None:
        harness = SWEBenchHarness(agent=lambda tc: True, dataset=SWE_DATASET)
        result = harness.evaluate()
        assert isinstance(result, SWEBenchResult)
        assert result.scaffold_pass_rate == pytest.approx(1.0)
        assert result.n_resolved == 5

    def test_unresolved_agent(self) -> None:
        harness = SWEBenchHarness(agent=lambda tc: False, dataset=SWE_DATASET)
        result = harness.evaluate()
        assert result.scaffold_pass_rate == pytest.approx(0.0)
        assert result.n_resolved == 0

    def test_float_output(self) -> None:
        harness = SWEBenchHarness(agent=lambda tc: 0.9, dataset=SWE_DATASET)
        result = harness.evaluate()
        assert result.n_resolved == 5

    def test_string_output(self) -> None:
        harness = SWEBenchHarness(agent=lambda tc: "resolved", dataset=SWE_DATASET)
        result = harness.evaluate()
        assert result.n_resolved == 5

    def test_empty_dataset_raises(self) -> None:
        harness = SWEBenchHarness(agent=lambda tc: True, dataset=[])
        with pytest.raises(ValueError, match="dataset must not be empty"):
            harness.evaluate()

    def test_instance_ids_captured(self) -> None:
        harness = SWEBenchHarness(agent=lambda tc: True, dataset=SWE_DATASET)
        result = harness.evaluate()
        assert len(result.instance_ids) == 5
        assert "repo__issue_0" in result.instance_ids

    def test_agent_exception_skipped(self) -> None:
        def _raise_agent(tc: dict[str, Any]) -> bool:
            raise RuntimeError("broken")

        harness = SWEBenchHarness(agent=_raise_agent, dataset=SWE_DATASET)
        result = harness.evaluate()
        assert result.n_resolved == 0
        assert result.n_instances == 5

    def test_is_resolved_variants(self) -> None:
        harness = SWEBenchHarness(agent=lambda tc: True, dataset=SWE_DATASET[:1])
        assert harness._is_resolved("resolved", {}) is True
        assert harness._is_resolved("true", {}) is True
        assert harness._is_resolved("pass", {}) is True
        assert harness._is_resolved("1", {}) is True
        assert harness._is_resolved("failed", {}) is False
        assert harness._is_resolved(0.9, {}) is True
        assert harness._is_resolved(0.3, {}) is False
