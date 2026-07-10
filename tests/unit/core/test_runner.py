"""Tests for run_suite, arun_suite, and concurrent_cancellation_probe."""

from __future__ import annotations

import asyncio
import itertools
import subprocess
import sys
import threading
import warnings
from pathlib import Path
from typing import Any

import pytest

from agent_regress.core.runner import (
    CACHE_BUST_NONCE_KEY,
    _default_cancel_indices,
    arun_suite,
    concurrent_cancellation_probe,
    run_suite,
    subprocess_runner,
)


def _fixed_agent(score: float) -> Any:
    def _agent(test_case: dict[str, Any]) -> float:
        return score

    return _agent


def _fixed_async_agent(score: float) -> Any:
    async def _agent(test_case: dict[str, Any]) -> float:
        return score

    return _agent


def test_cache_bust_nonce_key_is_importable_and_stable() -> None:
    assert CACHE_BUST_NONCE_KEY == "_cache_bust_nonce"


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

    def test_cache_bust_key_fn_augments_test_case(
        self, basic_test_suite: list[dict[str, Any]]
    ) -> None:
        seen_cases: list[dict[str, Any]] = []

        def _agent(tc: dict[str, Any]) -> float:
            seen_cases.append(dict(tc))
            return 0.5

        def _cache_bust(tc: dict[str, Any], run_index: int) -> dict[str, Any]:
            return {"_cache_bust": f"{tc['query']}-{run_index}"}

        run_suite(_agent, basic_test_suite, n_runs=3, cache_bust_key_fn=_cache_bust)

        assert len(seen_cases) == len(basic_test_suite) * 3
        assert all("_cache_bust" in case for case in seen_cases)
        # Original keys are preserved alongside the injected nonce.
        assert all("query" in case and "expected" in case for case in seen_cases)
        # The nonce values are distinct per run for a given test case.
        nonces_for_first_query = {
            case["_cache_bust"] for case in seen_cases if case["query"] == "question_0"
        }
        assert len(nonces_for_first_query) == 3

    def test_cache_bust_key_fn_none_preserves_raw_test_case(
        self, basic_test_suite: list[dict[str, Any]]
    ) -> None:
        seen_cases: list[dict[str, Any]] = []

        def _agent(tc: dict[str, Any]) -> float:
            seen_cases.append(tc)
            return 0.5

        run_suite(_agent, basic_test_suite, n_runs=2, cache_bust_key_fn=None)

        assert all(set(case.keys()) == {"query", "expected"} for case in seen_cases)

    def test_cache_bust_key_fn_default_preserves_current_behavior(
        self, basic_test_suite: list[dict[str, Any]]
    ) -> None:
        seen_cases: list[dict[str, Any]] = []

        def _agent(tc: dict[str, Any]) -> float:
            seen_cases.append(tc)
            return 0.5

        run_suite(_agent, basic_test_suite, n_runs=2)

        assert all(set(case.keys()) == {"query", "expected"} for case in seen_cases)

    def test_scorer_receives_original_test_case_not_augmented(
        self, basic_test_suite: list[dict[str, Any]]
    ) -> None:
        seen_scorer_cases: list[dict[str, Any]] = []

        def _agent(tc: dict[str, Any]) -> str:
            return "answer"

        def _scorer(output: Any, tc: dict[str, Any]) -> float:
            seen_scorer_cases.append(tc)
            return 0.9

        def _cache_bust(tc: dict[str, Any], run_index: int) -> dict[str, Any]:
            return {"_cache_bust": run_index}

        run_suite(
            _agent,
            basic_test_suite,
            n_runs=2,
            scorer=_scorer,
            cache_bust_key_fn=_cache_bust,
        )

        assert all("_cache_bust" not in case for case in seen_scorer_cases)

    def test_near_zero_variance_warns_when_n_runs_meets_threshold(
        self, basic_test_suite: list[dict[str, Any]]
    ) -> None:
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            run_suite(_fixed_agent(0.5), basic_test_suite, n_runs=10)
            assert any("SUT-side caching" in str(warning.message) for warning in w)

    def test_near_zero_variance_no_warning_below_n_runs_threshold(
        self, basic_test_suite: list[dict[str, Any]]
    ) -> None:
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            run_suite(_fixed_agent(0.5), basic_test_suite, n_runs=9)
            assert not any("SUT-side caching" in str(warning.message) for warning in w)

    def test_near_zero_variance_no_warning_when_scores_vary(
        self, basic_test_suite: list[dict[str, Any]]
    ) -> None:
        counter = {"n": 0}

        def _varying_agent(tc: dict[str, Any]) -> float:
            counter["n"] += 1
            return 0.5 + (counter["n"] % 2) * 0.01

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            run_suite(_varying_agent, basic_test_suite, n_runs=10)
            assert not any("SUT-side caching" in str(warning.message) for warning in w)

    def test_near_zero_variance_warns_on_near_identical_non_byte_identical_scores(
        self, basic_test_suite: list[dict[str, Any]]
    ) -> None:
        """Range-based check catches near-duplicate floats the old
        exact-set check (`len(set(all_scores)) == 1`) would have missed,
        since these scores are all distinct Python floats (not byte-identical)
        but differ from each other by far less than any practically
        meaningful variance.
        """
        counter = itertools.count(1)

        def _near_identical_agent(tc: dict[str, Any]) -> float:
            return 0.8 + next(counter) * 1e-11

        scores = []
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            scores = run_suite(_near_identical_agent, basic_test_suite, n_runs=10)
            # Sanity: the old exact-set check would NOT have fired, because
            # these scores are not byte-identical.
            assert len(set(scores)) > 1
            assert any("SUT-side caching" in str(warning.message) for warning in w)

    def test_stateful_param_default_preserves_behavior(
        self, basic_test_suite: list[dict[str, Any]]
    ) -> None:
        scores_default = run_suite(_fixed_agent(0.8), basic_test_suite, n_runs=3)
        scores_stateful_true = run_suite(
            _fixed_agent(0.8), basic_test_suite, n_runs=3, stateful=True
        )
        assert scores_default == scores_stateful_true

    def test_stateful_true_no_intra_case_parallelism(
        self, basic_test_suite: list[dict[str, Any]]
    ) -> None:
        """A test case's n_runs calls all land on the same OS thread.

        Records (test_case_id, call_index, thread_id) tuples via
        threading.get_ident() and asserts that, for each logical test case,
        every recorded call shares a single thread id -- proving the n_runs
        loop for one test case is never interleaved across threads.
        """
        lock = threading.Lock()
        records: list[tuple[int, int, int]] = []
        call_counters: dict[int, int] = {}

        def _recording_agent(test_case: dict[str, Any]) -> float:
            case_id = id(test_case)
            with lock:
                call_index = call_counters.get(case_id, 0)
                call_counters[case_id] = call_index + 1
                records.append((case_id, call_index, threading.get_ident()))
            return 0.5

        run_suite(
            _recording_agent,
            basic_test_suite,
            n_runs=20,
            stateful=True,
            max_workers=8,
        )

        assert len(records) == len(basic_test_suite) * 20

        by_case: dict[int, list[tuple[int, int]]] = {}
        for case_id, call_index, thread_id in records:
            by_case.setdefault(case_id, []).append((call_index, thread_id))

        assert len(by_case) == len(basic_test_suite)
        for case_id, entries in by_case.items():
            thread_ids_for_case = {thread_id for _call_index, thread_id in entries}
            assert len(thread_ids_for_case) == 1, (
                f"test case {case_id} had calls on multiple threads: "
                f"{thread_ids_for_case}"
            )
            # And the calls for this case were sequential 0..n_runs-1, each
            # index appearing exactly once (no duplicate/skip from a race).
            call_indices = sorted(call_index for call_index, _tid in entries)
            assert call_indices == list(range(20))


class TestArunSuite:
    def test_basic_run(self, basic_test_suite: list[dict[str, Any]]) -> None:
        scores = asyncio.run(
            arun_suite(_fixed_async_agent(0.8), basic_test_suite, n_runs=3)
        )
        assert len(scores) == 5 * 3
        assert all(s == 0.8 for s in scores)

    def test_returns_floats(self, basic_test_suite: list[dict[str, Any]]) -> None:
        scores = asyncio.run(
            arun_suite(_fixed_async_agent(1), basic_test_suite, n_runs=2)
        )
        assert all(isinstance(s, float) for s in scores)

    def test_empty_test_suite_raises(self) -> None:
        with pytest.raises(ValueError, match="test_suite must not be empty"):
            asyncio.run(arun_suite(_fixed_async_agent(0.8), [], n_runs=5))

    def test_zero_runs_raises(self, basic_test_suite: list[dict[str, Any]]) -> None:
        with pytest.raises(ValueError, match="n_runs must be >= 1"):
            asyncio.run(arun_suite(_fixed_async_agent(0.8), basic_test_suite, n_runs=0))

    def test_non_callable_raises(self, basic_test_suite: list[dict[str, Any]]) -> None:
        with pytest.raises(TypeError, match="agent must be callable"):
            asyncio.run(
                arun_suite("not_callable", basic_test_suite, n_runs=2)  # type: ignore[arg-type]
            )

    def test_max_concurrency_zero_raises(
        self, basic_test_suite: list[dict[str, Any]]
    ) -> None:
        with pytest.raises(ValueError, match="max_concurrency must be >= 1"):
            asyncio.run(
                arun_suite(
                    _fixed_async_agent(0.8),
                    basic_test_suite,
                    n_runs=2,
                    max_concurrency=0,
                )
            )

    def test_warns_on_low_n_runs(self, basic_test_suite: list[dict[str, Any]]) -> None:
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            asyncio.run(arun_suite(_fixed_async_agent(0.8), basic_test_suite, n_runs=3))
            assert any(issubclass(warning.category, UserWarning) for warning in w)

    def test_custom_scorer(self, basic_test_suite: list[dict[str, Any]]) -> None:
        async def _agent(tc: dict[str, Any]) -> str:
            return "answer"

        def _scorer(output: Any, tc: dict[str, Any]) -> float:
            return 0.9

        scores = asyncio.run(
            arun_suite(_agent, basic_test_suite, n_runs=2, scorer=_scorer)
        )
        assert all(s == 0.9 for s in scores)

    def test_non_float_output_without_scorer_raises(
        self, basic_test_suite: list[dict[str, Any]]
    ) -> None:
        async def _str_agent(tc: dict[str, Any]) -> str:
            return "some text"

        with pytest.raises(TypeError, match="scorer="):
            asyncio.run(arun_suite(_str_agent, basic_test_suite, n_runs=2))

    def test_score_clamping_warns(self, basic_test_suite: list[dict[str, Any]]) -> None:
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            asyncio.run(arun_suite(_fixed_async_agent(1.5), basic_test_suite, n_runs=2))
            assert any("Clamping" in str(warning.message) for warning in w)

    def test_near_zero_variance_warns(
        self, basic_test_suite: list[dict[str, Any]]
    ) -> None:
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            asyncio.run(
                arun_suite(_fixed_async_agent(0.5), basic_test_suite, n_runs=10)
            )
            assert any(
                "identical across every" in str(warning.message) for warning in w
            )

    def test_default_allows_intra_case_concurrency(self) -> None:
        """Without stateful=True, one test case's own n_runs calls may overlap.

        This is the key behavioral difference from run_suite(), whose
        thread-per-case design makes sequential-per-case execution hold
        unconditionally; arun_suite()'s default flat asyncio.gather does not.
        """
        active_count = {"n": 0}
        max_active = {"n": 0}

        async def _agent(tc: dict[str, Any]) -> float:
            active_count["n"] += 1
            max_active["n"] = max(max_active["n"], active_count["n"])
            await asyncio.sleep(0.01)
            active_count["n"] -= 1
            return 0.5

        single_case = [{"query": "only_one"}]
        asyncio.run(arun_suite(_agent, single_case, n_runs=5))

        assert max_active["n"] > 1

    def test_stateful_true_no_intra_case_interleaving(
        self, basic_test_suite: list[dict[str, Any]]
    ) -> None:
        active: dict[int, bool] = {}
        violations: list[int] = []
        call_counts: dict[int, int] = {}

        async def _agent(tc: dict[str, Any]) -> float:
            case_id = id(tc)
            if active.get(case_id):
                violations.append(case_id)
            active[case_id] = True
            await asyncio.sleep(0.001)
            active[case_id] = False
            call_counts[case_id] = call_counts.get(case_id, 0) + 1
            return 0.5

        scores = asyncio.run(
            arun_suite(_agent, basic_test_suite, n_runs=5, stateful=True)
        )

        assert violations == []
        assert len(scores) == len(basic_test_suite) * 5
        assert all(count == 5 for count in call_counts.values())

    def test_max_concurrency_bounds_all_calls(
        self, basic_test_suite: list[dict[str, Any]]
    ) -> None:
        active_count = {"n": 0}
        max_active = {"n": 0}

        async def _agent(tc: dict[str, Any]) -> float:
            active_count["n"] += 1
            max_active["n"] = max(max_active["n"], active_count["n"])
            await asyncio.sleep(0.01)
            active_count["n"] -= 1
            return 0.5

        asyncio.run(arun_suite(_agent, basic_test_suite, n_runs=5, max_concurrency=2))

        assert max_active["n"] <= 2

    def test_max_concurrency_bounds_stateful_run_too(
        self, basic_test_suite: list[dict[str, Any]]
    ) -> None:
        active_count = {"n": 0}
        max_active = {"n": 0}

        async def _agent(tc: dict[str, Any]) -> float:
            active_count["n"] += 1
            max_active["n"] = max(max_active["n"], active_count["n"])
            await asyncio.sleep(0.01)
            active_count["n"] -= 1
            return 0.5

        asyncio.run(
            arun_suite(
                _agent, basic_test_suite, n_runs=3, stateful=True, max_concurrency=2
            )
        )

        assert max_active["n"] <= 2


class TestConcurrentCancellationProbe:
    def test_default_cancel_indices_formula(self) -> None:
        assert _default_cancel_indices(10, 0.3) == {0, 3, 6, 9}
        assert _default_cancel_indices(10, 1.0) == set(range(10))
        assert _default_cancel_indices(10, 0.0) == set()

    def test_no_cancellation_all_complete(self) -> None:
        async def _agent(tc: dict[str, Any]) -> float:
            await asyncio.sleep(0.001)
            return 1.0

        result = asyncio.run(
            concurrent_cancellation_probe(
                _agent, {"query": "x"}, n_concurrent=5, cancel_indices=set()
            )
        )
        assert result == {"completed": 5, "cancelled": 0, "failed": 0}

    def test_cancellation_observable_via_slow_agent(self) -> None:
        order_counter = itertools.count()

        async def _agent(tc: dict[str, Any]) -> int:
            idx = next(order_counter)
            await asyncio.sleep(0.05)
            return idx

        result = asyncio.run(
            concurrent_cancellation_probe(
                _agent, {"query": "x"}, n_concurrent=6, cancel_indices={1, 3}
            )
        )
        assert result == {"completed": 4, "cancelled": 2, "failed": 0}

    def test_default_cancel_fraction_used_when_indices_omitted(self) -> None:
        order_counter = itertools.count()

        async def _agent(tc: dict[str, Any]) -> int:
            idx = next(order_counter)
            await asyncio.sleep(0.05)
            return idx

        result = asyncio.run(
            concurrent_cancellation_probe(
                _agent, {"query": "x"}, n_concurrent=10, cancel_fraction=0.3
            )
        )
        # step = round(1/0.3) = 3 -> indices {0, 3, 6, 9} cancelled
        assert result == {"completed": 6, "cancelled": 4, "failed": 0}

    def test_failed_calls_counted_separately_from_cancelled(self) -> None:
        counter = itertools.count()

        async def _agent(tc: dict[str, Any]) -> float:
            idx = next(counter)
            if idx == 2:
                raise ValueError("boom")
            await asyncio.sleep(0.01)
            return 1.0

        result = asyncio.run(
            concurrent_cancellation_probe(
                _agent, {"query": "x"}, n_concurrent=5, cancel_indices=set()
            )
        )
        assert result["failed"] == 1
        assert result["completed"] == 4
        assert result["cancelled"] == 0

    def test_out_of_range_cancel_indices_are_ignored(self) -> None:
        async def _agent(tc: dict[str, Any]) -> float:
            await asyncio.sleep(0.001)
            return 1.0

        result = asyncio.run(
            concurrent_cancellation_probe(
                _agent,
                {"query": "x"},
                n_concurrent=4,
                cancel_indices={-1, 99},
            )
        )
        assert result == {"completed": 4, "cancelled": 0, "failed": 0}

    def test_non_callable_agent_raises(self) -> None:
        with pytest.raises(TypeError, match="agent must be callable"):
            asyncio.run(
                concurrent_cancellation_probe(
                    "not_callable",  # type: ignore[arg-type]
                    {"query": "x"},
                    n_concurrent=3,
                )
            )

    def test_n_concurrent_zero_raises(self) -> None:
        async def _agent(tc: dict[str, Any]) -> float:
            return 1.0

        with pytest.raises(ValueError, match="n_concurrent must be >= 1"):
            asyncio.run(
                concurrent_cancellation_probe(_agent, {"query": "x"}, n_concurrent=0)
            )

    def test_cancel_fraction_out_of_range_raises(self) -> None:
        async def _agent(tc: dict[str, Any]) -> float:
            return 1.0

        with pytest.raises(ValueError, match="cancel_fraction must be in"):
            asyncio.run(
                concurrent_cancellation_probe(
                    _agent, {"query": "x"}, n_concurrent=3, cancel_fraction=1.5
                )
            )


class TestSubprocessRunner:
    def test_returns_parsed_json_result(self, tmp_path: Path) -> None:
        script = tmp_path / "runner_v1.py"
        script.write_text(
            "import sys, json\n"
            "tc = json.loads(sys.stdin.read())\n"
            'print(json.dumps({"output": tc["query"] + "_v1"}))\n'
        )

        agent = subprocess_runner(sys.executable, str(script))
        result = agent({"query": "hello"})

        assert result == {"output": "hello_v1"}

    def test_passes_full_test_case_through_stdin(self, tmp_path: Path) -> None:
        script = tmp_path / "echo_runner.py"
        script.write_text(
            "import sys, json\n"
            "tc = json.loads(sys.stdin.read())\n"
            "print(json.dumps(tc))\n"
        )

        agent = subprocess_runner(sys.executable, str(script))
        test_case = {"query": "q", "expected": "e", "nested": {"a": 1}}
        result = agent(test_case)

        assert result == test_case

    def test_nonzero_exit_raises_runtime_error_with_stderr(
        self, tmp_path: Path
    ) -> None:
        script = tmp_path / "failing_runner.py"
        script.write_text(
            'import sys\nsys.stderr.write("boom: something went wrong")\nsys.exit(1)\n'
        )

        agent = subprocess_runner(sys.executable, str(script))

        with pytest.raises(RuntimeError, match="boom: something went wrong"):
            agent({"query": "hello"})

    def test_timeout_raises(self, tmp_path: Path) -> None:
        script = tmp_path / "slow_runner.py"
        script.write_text(
            "import sys, time, json\n"
            "sys.stdin.read()\n"
            "time.sleep(5)\n"
            'print(json.dumps({"output": "too_late"}))\n'
        )

        agent = subprocess_runner(sys.executable, str(script), timeout=0.1)

        with pytest.raises(subprocess.TimeoutExpired):
            agent({"query": "hello"})
