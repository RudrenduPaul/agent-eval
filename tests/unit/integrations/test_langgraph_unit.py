"""Unit tests for the LangGraph integration, using a duck-typed fake graph.

These tests monkeypatch `sys.modules["langgraph"]` so they run without a real
langgraph install (langgraph is not importable in this dev venv — see repo
notes).
"""

from __future__ import annotations

import asyncio
import sys
from types import SimpleNamespace
from typing import Any, ClassVar
from unittest.mock import MagicMock

import pytest

from agent_regress.core.runner import CACHE_BUST_NONCE_KEY
from agent_regress.integrations.langgraph import (
    _build_state,
    graph_has_cache,
    langgraph_async_runner,
    langgraph_interrupt_resume_runner,
    langgraph_runner,
)


@pytest.fixture(autouse=True)
def _fake_langgraph_module(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setitem(sys.modules, "langgraph", MagicMock())


class _FakeCommand:
    """Fake `langgraph.types.Command`, recording the resume value it got."""

    def __init__(self, resume: Any = None) -> None:
        self.resume = resume


@pytest.fixture(autouse=True)
def _fake_langgraph_types_module(monkeypatch: pytest.MonkeyPatch) -> None:
    """Fake `langgraph.types` exposing a fake `Command`.

    `langgraph_interrupt_resume_runner()` does `from langgraph.types import
    Command`; since `sys.modules["langgraph"]` is faked to a bare MagicMock
    (no real `__path__`), the submodule import must also be pre-registered
    in `sys.modules` or Python's import machinery would try (and fail) to
    resolve `langgraph.types` against the fake package.
    """
    monkeypatch.setitem(
        sys.modules, "langgraph.types", SimpleNamespace(Command=_FakeCommand)
    )


class _FakeGraph:
    """Duck-typed fake compiled graph recording every .invoke() call."""

    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    def invoke(
        self, state: dict[str, Any], config: dict[str, Any] | None = None
    ) -> Any:
        self.calls.append({"state": state, "config": config})
        return {"result": "ok", "call_index": len(self.calls) - 1}


class _FakeGraphWithContext:
    """Fake graph whose .invoke() accepts both config= and context=."""

    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    def invoke(
        self,
        state: dict[str, Any],
        config: dict[str, Any] | None = None,
        context: dict[str, Any] | None = None,
    ) -> Any:
        self.calls.append({"state": state, "config": config, "context": context})
        return {"result": "ok"}


class _FakeCheckpointGraph:
    """Fake graph exposing checkpoint-surgery methods (no .invoke needed here)."""

    def __init__(self) -> None:
        self.bulk_update_calls: list[tuple[Any, Any]] = []
        self.update_state_calls: list[tuple[Any, Any]] = []
        self.get_state_calls: list[Any] = []

    def invoke(
        self, state: dict[str, Any], config: dict[str, Any] | None = None
    ) -> Any:
        raise AssertionError("invoke() should not be called when operation= is set")

    def bulk_update_state(self, config: Any, updates: Any) -> str:
        self.bulk_update_calls.append((config, updates))
        return "bulk-updated"

    def update_state(self, config: Any, values: Any) -> str:
        self.update_state_calls.append((config, values))
        return "updated"

    def get_state(self, config: Any) -> str:
        self.get_state_calls.append(config)
        return "state-snapshot"


class _FakeAsyncGraph:
    """Duck-typed fake compiled graph recording every .ainvoke() call."""

    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    async def ainvoke(
        self,
        state: dict[str, Any],
        config: dict[str, Any] | None = None,
        context: dict[str, Any] | None = None,
    ) -> Any:
        self.calls.append({"state": state, "config": config, "context": context})
        return {"result": "ok", "call_index": len(self.calls) - 1}


class _FakeAsyncCheckpointGraph:
    """Fake async graph exposing checkpoint-surgery methods (no .ainvoke needed here)."""

    def __init__(self) -> None:
        self.bulk_update_calls: list[tuple[Any, Any]] = []

    async def ainvoke(
        self, state: dict[str, Any], config: dict[str, Any] | None = None
    ) -> Any:
        raise AssertionError("ainvoke() should not be called when operation= is set")

    async def abulk_update_state(self, config: Any, updates: Any) -> str:
        self.bulk_update_calls.append((config, updates))
        return "bulk-updated"


class _FakeSnapshot:
    """Fake `langgraph.types.StateSnapshot` (the fields this integration reads)."""

    def __init__(
        self,
        next_nodes: tuple[str, ...] = (),
        interrupts: tuple[Any, ...] = (),
        tasks: tuple[Any, ...] = (),
    ) -> None:
        self.next = next_nodes
        self.interrupts = interrupts
        self.tasks = tasks


class _FakeTask:
    """Fake `langgraph.types.PregelTask` (only the `.interrupts` field matters here)."""

    def __init__(self, interrupts: tuple[Any, ...] = ()) -> None:
        self.interrupts = interrupts


class _FakeInterruptResumeGraph:
    """Fake graph exercising the interrupt-then-resume cycle.

    First `.invoke()` call always returns a single `call-1` tool message.
    `.get_state()` reports interrupted (or not) per `interrupted_after_first_invoke`.
    A second `.invoke()` call (the resume, called with a `Command` instance
    as `state`) returns a `call-1` + `call-2` trace by default — override via
    subclassing to simulate a buggy double-execution.
    """

    def __init__(self, interrupted_after_first_invoke: bool) -> None:
        self.invoke_calls: list[dict[str, Any]] = []
        self.get_state_calls: list[dict[str, Any] | None] = []
        self.interrupted_after_first_invoke = interrupted_after_first_invoke

    def invoke(self, state: Any, config: dict[str, Any] | None = None) -> Any:
        call_index = len(self.invoke_calls)
        self.invoke_calls.append({"state": state, "config": config})
        if call_index == 0:
            return {"messages": [{"tool_call_id": "call-1"}], "call_index": call_index}
        return {
            "messages": [{"tool_call_id": "call-1"}, {"tool_call_id": "call-2"}],
            "call_index": call_index,
        }

    def get_state(self, config: dict[str, Any] | None) -> _FakeSnapshot:
        self.get_state_calls.append(config)
        if self.interrupted_after_first_invoke:
            return _FakeSnapshot(
                next_nodes=("tool_node",),
                interrupts=({"value": "paused"},),
                tasks=(_FakeTask(interrupts=({"value": "paused"},)),),
            )
        return _FakeSnapshot()


class TestBackwardCompatibility:
    def test_default_behavior_matches_original_invoke_only(self) -> None:
        graph = _FakeGraph()
        agent = langgraph_runner(graph)
        result = agent({"messages": ["hi"]})
        assert result == {"result": "ok", "call_index": 0}
        assert graph.calls == [{"state": {"messages": ["hi"]}, "config": None}]

    def test_falls_back_to_full_test_case_when_input_key_missing(self) -> None:
        graph = _FakeGraph()
        agent = langgraph_runner(graph, input_key="messages")
        test_case = {"other_key": "value"}
        agent(test_case)
        assert graph.calls[0]["state"] == test_case

    def test_custom_input_key(self) -> None:
        graph = _FakeGraph()
        agent = langgraph_runner(graph, input_key="query")
        agent({"query": "hello", "expected": "world"})
        assert graph.calls[0]["state"] == {"query": "hello"}


class TestBuildStateCacheBustNonce:
    """`_build_state()` must preserve CACHE_BUST_NONCE_KEY through narrowing.

    Regression test for the bug reported by @nfcampos: when `input_key` is
    present in `test_case`, `_build_state()` used to return only
    `{input_key: ...}`, silently dropping every other key — including a
    cache-bust nonce injected by `run_suite(cache_bust_key_fn=...)` under
    `CACHE_BUST_NONCE_KEY`. That defeated cache-busting for any LangGraph
    runner whose test cases carry `input_key`.
    """

    def test_nonce_preserved_alongside_input_key_when_both_present(self) -> None:
        test_case = {
            "messages": ["hi"],
            "expected": "ignored",
            CACHE_BUST_NONCE_KEY: "nonce-123",
        }
        state = _build_state(test_case, "messages")
        assert state == {
            "messages": ["hi"],
            CACHE_BUST_NONCE_KEY: "nonce-123",
        }

    def test_narrowing_unchanged_when_nonce_absent(self) -> None:
        test_case = {"messages": ["hi"], "expected": "ignored"}
        state = _build_state(test_case, "messages")
        assert state == {"messages": ["hi"]}
        assert CACHE_BUST_NONCE_KEY not in state

    def test_full_test_case_passthrough_unaffected_when_input_key_missing(
        self,
    ) -> None:
        test_case = {"other_key": "value", CACHE_BUST_NONCE_KEY: "nonce-456"}
        state = _build_state(test_case, "messages")
        assert state is test_case
        assert state[CACHE_BUST_NONCE_KEY] == "nonce-456"

    def test_nonce_flows_through_langgraph_runner_invoke(self) -> None:
        graph = _FakeGraph()
        agent = langgraph_runner(graph, input_key="messages")
        test_case = {
            "messages": ["hi"],
            CACHE_BUST_NONCE_KEY: "nonce-789",
        }
        agent(test_case)
        assert graph.calls[0]["state"] == {
            "messages": ["hi"],
            CACHE_BUST_NONCE_KEY: "nonce-789",
        }

    def test_nonce_flows_through_langgraph_async_runner_ainvoke(self) -> None:
        graph = _FakeAsyncGraph()
        agent = langgraph_async_runner(graph, input_key="messages")
        test_case = {
            "messages": ["hi"],
            CACHE_BUST_NONCE_KEY: "nonce-async",
        }
        asyncio.run(agent(test_case))
        assert graph.calls[0]["state"] == {
            "messages": ["hi"],
            CACHE_BUST_NONCE_KEY: "nonce-async",
        }


class TestConfigContextPassthrough:
    def test_config_passed_through_on_every_call(self) -> None:
        graph = _FakeGraph()
        config = {"configurable": {"model": "gpt-4o"}}
        agent = langgraph_runner(graph, config=config)
        agent({"messages": ["a"]})
        agent({"messages": ["b"]})
        assert graph.calls[0]["config"] == config
        assert graph.calls[1]["config"] == config

    def test_config_not_mutated_by_caller_dict_identity(self) -> None:
        graph = _FakeGraph()
        config = {"configurable": {"model": "gpt-4o"}}
        agent = langgraph_runner(graph, config=config)
        agent({"messages": ["a"]})
        # Original dict passed by caller must remain untouched.
        assert config == {"configurable": {"model": "gpt-4o"}}

    def test_context_forwarded_when_invoke_supports_it(self) -> None:
        graph = _FakeGraphWithContext()
        context = {"user_id": "u1"}
        agent = langgraph_runner(graph, context=context)
        agent({"messages": ["hi"]})
        assert graph.calls[0]["context"] == context

    def test_context_silently_dropped_when_invoke_does_not_support_it(self) -> None:
        graph = _FakeGraph()  # .invoke() has no context= parameter
        agent = langgraph_runner(graph, context={"user_id": "u1"})
        # Should not raise TypeError even though invoke() can't accept context=.
        result = agent({"messages": ["hi"]})
        assert result == {"result": "ok", "call_index": 0}
        assert "context" not in graph.calls[0] or graph.calls[0].get("context") is None


class TestThreadAware:
    def test_thread_id_stable_across_calls_for_same_test_case(self) -> None:
        graph = _FakeGraph()
        agent = langgraph_runner(graph, thread_aware=True)
        test_case = {"messages": ["hi"]}
        agent(test_case)
        agent(test_case)
        agent(test_case)
        thread_ids = [c["config"]["configurable"]["thread_id"] for c in graph.calls]
        assert len(set(thread_ids)) == 1

    def test_thread_id_differs_across_distinct_test_cases(self) -> None:
        graph = _FakeGraph()
        agent = langgraph_runner(graph, thread_aware=True)
        tc_a = {"messages": ["a"]}
        tc_b = {"messages": ["b"]}
        agent(tc_a)
        agent(tc_b)
        thread_id_a = graph.calls[0]["config"]["configurable"]["thread_id"]
        thread_id_b = graph.calls[1]["config"]["configurable"]["thread_id"]
        assert thread_id_a != thread_id_b

    def test_thread_id_factory_used_when_provided(self) -> None:
        graph = _FakeGraph()
        counter = iter(["thread-alpha", "thread-beta"])
        agent = langgraph_runner(
            graph, thread_aware=True, thread_id_factory=lambda: next(counter)
        )
        agent({"messages": ["a"]})
        assert graph.calls[0]["config"]["configurable"]["thread_id"] == "thread-alpha"

    def test_thread_aware_preserves_existing_config(self) -> None:
        graph = _FakeGraph()
        base_config = {"configurable": {"model": "gpt-4o"}, "tags": ["v1"]}
        agent = langgraph_runner(graph, config=base_config, thread_aware=True)
        agent({"messages": ["a"]})
        call_config = graph.calls[0]["config"]
        assert call_config["configurable"]["model"] == "gpt-4o"
        assert call_config["tags"] == ["v1"]
        assert "thread_id" in call_config["configurable"]
        # Original base_config untouched.
        assert "thread_id" not in base_config["configurable"]

    def test_default_no_thread_aware_no_thread_id_injected(self) -> None:
        graph = _FakeGraph()
        agent = langgraph_runner(graph)
        agent({"messages": ["a"]})
        assert graph.calls[0]["config"] is None


class TestOperationHook:
    def test_operation_called_instead_of_invoke(self) -> None:
        graph = _FakeCheckpointGraph()
        test_case = {
            "config": {"configurable": {"thread_id": "t1"}},
            "updates": [({}, {})],
        }
        agent = langgraph_runner(
            graph,
            operation=lambda g, tc: g.bulk_update_state(tc["config"], tc["updates"]),
        )
        result = agent(test_case)
        assert result == "bulk-updated"
        assert graph.bulk_update_calls == [(test_case["config"], test_case["updates"])]

    def test_operation_receives_raw_graph_and_test_case(self) -> None:
        graph = _FakeCheckpointGraph()
        test_case = {"config": "cfg-1"}
        agent = langgraph_runner(
            graph, operation=lambda g, tc: g.get_state(tc["config"])
        )
        result = agent(test_case)
        assert result == "state-snapshot"
        assert graph.get_state_calls == ["cfg-1"]

    def test_operation_bypasses_invoke_entirely(self) -> None:
        graph = _FakeCheckpointGraph()
        agent = langgraph_runner(
            graph,
            operation=lambda g, tc: g.update_state(tc["config"], tc["values"]),
        )
        # graph.invoke would raise AssertionError if called; this must not raise.
        result = agent({"config": "cfg-1", "values": {"foo": "bar"}})
        assert result == "updated"

    def test_operation_none_default_uses_invoke(self) -> None:
        graph = _FakeGraph()
        agent = langgraph_runner(graph, operation=None)
        result = agent({"messages": ["hi"]})
        assert result == {"result": "ok", "call_index": 0}


class TestLanggraphAsyncRunner:
    def test_default_behavior_calls_ainvoke_with_state_and_config(self) -> None:
        graph = _FakeAsyncGraph()
        agent = langgraph_async_runner(graph)
        result = asyncio.run(agent({"messages": ["hi"]}))
        assert result == {"result": "ok", "call_index": 0}
        assert graph.calls == [
            {"state": {"messages": ["hi"]}, "config": None, "context": None}
        ]

    def test_falls_back_to_full_test_case_when_input_key_missing(self) -> None:
        graph = _FakeAsyncGraph()
        agent = langgraph_async_runner(graph, input_key="messages")
        test_case = {"other_key": "value"}
        asyncio.run(agent(test_case))
        assert graph.calls[0]["state"] == test_case

    def test_custom_input_key(self) -> None:
        graph = _FakeAsyncGraph()
        agent = langgraph_async_runner(graph, input_key="query")
        asyncio.run(agent({"query": "hello", "expected": "world"}))
        assert graph.calls[0]["state"] == {"query": "hello"}

    def test_config_passed_through_on_every_call(self) -> None:
        graph = _FakeAsyncGraph()
        config = {"configurable": {"model": "gpt-4o"}}
        agent = langgraph_async_runner(graph, config=config)
        asyncio.run(agent({"messages": ["a"]}))
        asyncio.run(agent({"messages": ["b"]}))
        assert graph.calls[0]["config"] == config
        assert graph.calls[1]["config"] == config

    def test_context_forwarded_when_given(self) -> None:
        graph = _FakeAsyncGraph()
        context = {"user_id": "u1"}
        agent = langgraph_async_runner(graph, context=context)
        asyncio.run(agent({"messages": ["hi"]}))
        assert graph.calls[0]["context"] == context

    def test_context_none_default_does_not_forward_context(self) -> None:
        graph = _FakeAsyncGraph()
        agent = langgraph_async_runner(graph)
        asyncio.run(agent({"messages": ["hi"]}))
        assert graph.calls[0]["context"] is None

    def test_store_stashed_under_config_configurable(self) -> None:
        graph = _FakeAsyncGraph()
        store = object()
        agent = langgraph_async_runner(graph, store=store)
        asyncio.run(agent({"messages": ["hi"]}))
        call_config = graph.calls[0]["config"]
        assert call_config is not None
        assert call_config["configurable"]["store"] is store

    def test_store_merged_with_existing_config_without_overwriting(self) -> None:
        graph = _FakeAsyncGraph()
        store = object()
        base_config = {"configurable": {"model": "gpt-4o"}, "tags": ["v1"]}
        agent = langgraph_async_runner(graph, store=store, config=base_config)
        asyncio.run(agent({"messages": ["hi"]}))
        call_config = graph.calls[0]["config"]
        assert call_config["configurable"]["model"] == "gpt-4o"
        assert call_config["configurable"]["store"] is store
        assert call_config["tags"] == ["v1"]
        # Original base_config dict passed by caller must remain untouched.
        assert "store" not in base_config["configurable"]

    def test_store_none_default_leaves_config_untouched(self) -> None:
        graph = _FakeAsyncGraph()
        config = {"configurable": {"model": "gpt-4o"}}
        agent = langgraph_async_runner(graph, config=config)
        asyncio.run(agent({"messages": ["hi"]}))
        assert graph.calls[0]["config"] == config
        assert "store" not in graph.calls[0]["config"]["configurable"]

    def test_multiple_calls_are_independently_awaitable(self) -> None:
        graph = _FakeAsyncGraph()
        agent = langgraph_async_runner(graph)

        async def _run_three() -> list[Any]:
            return await asyncio.gather(
                agent({"messages": ["a"]}),
                agent({"messages": ["b"]}),
                agent({"messages": ["c"]}),
            )

        results = asyncio.run(_run_three())
        assert len(results) == 3
        assert len(graph.calls) == 3

    def test_works_with_arun_suite(self) -> None:
        from agent_regress.core.runner import arun_suite

        graph = _FakeAsyncGraph()
        agent = langgraph_async_runner(graph)
        test_suite = [{"messages": ["a"]}, {"messages": ["b"]}]

        def scorer(_output: Any, _tc: dict[str, Any]) -> float:
            return 1.0

        scores = asyncio.run(
            arun_suite(agent, test_suite, n_runs=3, scorer=scorer, max_concurrency=2)
        )
        assert scores == [1.0] * 6
        assert len(graph.calls) == 6


class TestAsyncOperationHook:
    def test_operation_called_instead_of_ainvoke(self) -> None:
        graph = _FakeAsyncCheckpointGraph()
        test_case = {
            "config": {"configurable": {"thread_id": "t1"}},
            "updates": [({}, {})],
        }
        agent = langgraph_async_runner(
            graph,
            operation=lambda g, tc: g.abulk_update_state(tc["config"], tc["updates"]),
        )
        result = asyncio.run(agent(test_case))
        assert result == "bulk-updated"
        assert graph.bulk_update_calls == [(test_case["config"], test_case["updates"])]

    def test_operation_bypasses_ainvoke_entirely(self) -> None:
        graph = _FakeAsyncCheckpointGraph()
        agent = langgraph_async_runner(
            graph,
            operation=lambda g, tc: g.abulk_update_state(tc["config"], tc["updates"]),
        )
        # graph.ainvoke would raise AssertionError if awaited; this must not raise.
        result = asyncio.run(agent({"config": "cfg-1", "updates": [({}, {})]}))
        assert result == "bulk-updated"

    def test_operation_none_default_uses_ainvoke(self) -> None:
        graph = _FakeAsyncGraph()
        agent = langgraph_async_runner(graph, operation=None)
        result = asyncio.run(agent({"messages": ["hi"]}))
        assert result == {"result": "ok", "call_index": 0}


class TestInterruptResumeRunner:
    def test_no_interrupt_single_invoke_no_resume(self) -> None:
        graph = _FakeInterruptResumeGraph(interrupted_after_first_invoke=False)
        agent = langgraph_interrupt_resume_runner(graph)
        result = agent({"messages": ["hi"]})

        assert len(graph.invoke_calls) == 1
        assert len(graph.get_state_calls) == 1
        assert result["interrupted"] is False
        assert result["result"] == {
            "messages": [{"tool_call_id": "call-1"}],
            "call_index": 0,
        }
        assert result["messages"] == [{"tool_call_id": "call-1"}]

    def test_interrupt_then_resume_invokes_twice_with_command(self) -> None:
        graph = _FakeInterruptResumeGraph(interrupted_after_first_invoke=True)
        agent = langgraph_interrupt_resume_runner(graph, resume_value="go-ahead")
        result = agent({"messages": ["hi"]})

        assert len(graph.invoke_calls) == 2
        assert result["interrupted"] is True

        resume_arg = graph.invoke_calls[1]["state"]
        assert isinstance(resume_arg, _FakeCommand)
        assert resume_arg.resume == "go-ahead"

        assert result["result"]["call_index"] == 1
        assert result["messages"] == [
            {"tool_call_id": "call-1"},
            {"tool_call_id": "call-2"},
        ]

    def test_returned_dict_shape(self) -> None:
        graph = _FakeInterruptResumeGraph(interrupted_after_first_invoke=False)
        agent = langgraph_interrupt_resume_runner(graph)
        result = agent({"messages": ["hi"]})

        assert set(result.keys()) == {"result", "interrupted", "messages"}
        assert isinstance(result["interrupted"], bool)

    def test_thread_id_stable_across_invoke_and_resume_calls(self) -> None:
        graph = _FakeInterruptResumeGraph(interrupted_after_first_invoke=True)
        agent = langgraph_interrupt_resume_runner(graph)
        agent({"messages": ["hi"]})

        thread_ids = {
            call["config"]["configurable"]["thread_id"] for call in graph.invoke_calls
        }
        get_state_thread_ids = {
            call["configurable"]["thread_id"] for call in graph.get_state_calls if call
        }
        assert len(thread_ids) == 1
        assert thread_ids == get_state_thread_ids

    def test_thread_id_differs_across_test_cases(self) -> None:
        graph = _FakeInterruptResumeGraph(interrupted_after_first_invoke=False)
        agent = langgraph_interrupt_resume_runner(graph)
        agent({"messages": ["a"]})
        agent({"messages": ["b"]})

        thread_id_a = graph.invoke_calls[0]["config"]["configurable"]["thread_id"]
        thread_id_b = graph.invoke_calls[1]["config"]["configurable"]["thread_id"]
        assert thread_id_a != thread_id_b

    def test_explicit_thread_id_in_config_is_preserved(self) -> None:
        graph = _FakeInterruptResumeGraph(interrupted_after_first_invoke=False)
        base_config = {"configurable": {"thread_id": "custom-thread"}}
        agent = langgraph_interrupt_resume_runner(graph, config=base_config)
        agent({"messages": ["hi"]})

        assert (
            graph.invoke_calls[0]["config"]["configurable"]["thread_id"]
            == "custom-thread"
        )
        # Original base_config dict passed by caller must remain untouched.
        assert base_config == {"configurable": {"thread_id": "custom-thread"}}

    def test_result_usable_with_tool_call_trace_scorer_for_double_execution(
        self,
    ) -> None:
        from agent_regress.core.scorer import tool_call_trace_scorer

        class _DoubleExecutionGraph(_FakeInterruptResumeGraph):
            def invoke(self, state: Any, config: dict[str, Any] | None = None) -> Any:
                call_index = len(self.invoke_calls)
                self.invoke_calls.append({"state": state, "config": config})
                if call_index == 0:
                    return {"messages": [{"tool_call_id": "call-1"}]}
                # Buggy node: re-executes call-1 instead of moving on.
                return {
                    "messages": [
                        {"tool_call_id": "call-1"},
                        {"tool_call_id": "call-1"},
                    ]
                }

        graph = _DoubleExecutionGraph(interrupted_after_first_invoke=True)
        agent = langgraph_interrupt_resume_runner(graph)
        result = agent({"messages": ["hi"]})

        test_case = {"expected_tool_call_ids": ["call-1"]}
        score = tool_call_trace_scorer(result, test_case)
        assert score == 0.0  # call-1 appears twice -> double-execution caught

    def test_no_double_execution_scores_full_marks(self) -> None:
        from agent_regress.core.scorer import tool_call_trace_scorer

        graph = _FakeInterruptResumeGraph(interrupted_after_first_invoke=True)
        agent = langgraph_interrupt_resume_runner(graph)
        result = agent({"messages": ["hi"]})

        test_case = {"expected_tool_call_ids": ["call-1", "call-2"]}
        score = tool_call_trace_scorer(result, test_case)
        assert score == 1.0


class TestImportGuard:
    def test_missing_langgraph_raises_import_error(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setitem(sys.modules, "langgraph", None)
        graph = _FakeGraph()
        with pytest.raises(
            ImportError, match="pip install agent-regress\\[langgraph\\]"
        ):
            langgraph_runner(graph)

    def test_missing_langgraph_raises_import_error_for_async_runner(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setitem(sys.modules, "langgraph", None)
        graph = _FakeAsyncGraph()
        with pytest.raises(
            ImportError, match="pip install agent-regress\\[langgraph\\]"
        ):
            langgraph_async_runner(graph)

    def test_missing_langgraph_raises_import_error_for_interrupt_resume_runner(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setitem(sys.modules, "langgraph", None)
        graph = _FakeInterruptResumeGraph(interrupted_after_first_invoke=False)
        with pytest.raises(
            ImportError, match="pip install agent-regress\\[langgraph\\]"
        ):
            langgraph_interrupt_resume_runner(graph)


class TestWithRunSuite:
    def test_thread_aware_agent_works_with_run_suite_stateful(self) -> None:
        from agent_regress.core.runner import run_suite

        graph = _FakeGraph()
        agent = langgraph_runner(graph, thread_aware=True)
        test_suite = [{"messages": ["only case"]}]

        def scorer(_output: Any, _tc: dict[str, Any]) -> float:
            return 1.0

        scores = run_suite(
            agent, test_suite, n_runs=5, scorer=scorer, stateful=True, max_workers=4
        )
        assert scores == [1.0] * 5
        thread_ids = {c["config"]["configurable"]["thread_id"] for c in graph.calls}
        assert len(thread_ids) == 1


def test_langgraph_runner_returns_callable_namespace_module_placeholder() -> None:
    # Sanity check the fixture-provided fake module import path works even
    # when sys.modules["langgraph"] is an arbitrary namespace, not MagicMock.
    graph = _FakeGraph()
    module = SimpleNamespace()
    import agent_regress.integrations.langgraph as lg_module

    del module  # unused placeholder to avoid accidental shadowing
    agent = lg_module.langgraph_runner(graph)
    assert callable(agent)


class TestGraphHasCache:
    """graph_has_cache() never imports langgraph, so no fake-module needed."""

    def test_no_cache_attrs_returns_false(self) -> None:
        class PlainGraph:
            pass

        assert graph_has_cache(PlainGraph()) is False

    def test_cache_attr_present_and_non_none_returns_true(self) -> None:
        class GraphWithCache:
            cache = object()

        assert graph_has_cache(GraphWithCache()) is True

    def test_cache_attr_present_but_none_returns_false(self) -> None:
        class GraphWithNullCache:
            cache = None
            _cache = None
            cache_policy = None

        assert graph_has_cache(GraphWithNullCache()) is False

    def test_private_cache_attr_returns_true(self) -> None:
        class GraphWithPrivateCache:
            _cache: ClassVar[dict[str, str]] = {"some": "cache-backend"}

        assert graph_has_cache(GraphWithPrivateCache()) is True

    def test_cache_policy_attr_returns_true(self) -> None:
        class GraphWithCachePolicy:
            cache_policy = "some-policy-object"

        assert graph_has_cache(GraphWithCachePolicy()) is True

    def test_cache_on_node_returns_true(self) -> None:
        class FakeNode:
            cache_policy = "ttl=60"

        class GraphWithCachedNode:
            nodes: ClassVar[dict[str, Any]] = {"my_node": FakeNode()}

        assert graph_has_cache(GraphWithCachedNode()) is True

    def test_no_cache_on_any_node_returns_false(self) -> None:
        class FakeNode:
            cache_policy = None

        class GraphWithUncachedNodes:
            nodes: ClassVar[dict[str, Any]] = {
                "my_node": FakeNode(),
                "other_node": FakeNode(),
            }

        assert graph_has_cache(GraphWithUncachedNodes()) is False

    def test_nodes_as_plain_list_without_values_method(self) -> None:
        class FakeNode:
            cache = "enabled"

        class GraphWithListNodes:
            nodes: ClassVar[list[Any]] = [FakeNode()]

        assert graph_has_cache(GraphWithListNodes()) is True

    def test_unrelated_object_returns_false_and_never_raises(self) -> None:
        assert graph_has_cache(object()) is False
        assert graph_has_cache(None) is False
        assert graph_has_cache(42) is False

    def test_real_compiled_graph_mock_without_cache(self) -> None:
        graph = _FakeGraph()
        assert graph_has_cache(graph) is False

    def test_real_compiled_graph_mock_with_cache(self) -> None:
        graph = _FakeGraph()
        graph.cache = MagicMock()  # type: ignore[attr-defined]
        assert graph_has_cache(graph) is True
