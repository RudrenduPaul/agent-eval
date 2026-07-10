"""Integration tests for OpenAI Agents SDK runner.

These tests require a real openai-agents installation and optionally a real
OpenAI API key. Run with: pytest tests/integration/ -m integration
"""

from __future__ import annotations

from typing import Any

import pytest


@pytest.mark.integration
def test_openai_agents_runner_import_error() -> None:
    try:
        import agents  # noqa: F401  # type: ignore[import-untyped]

        pytest.skip("openai-agents installed, skipping import error test")
    except ImportError:
        from agent_regress.integrations.openai_agents import openai_agents_runner

        with pytest.raises(ImportError, match="openai-agents"):
            openai_agents_runner(object())


@pytest.mark.integration
def test_openai_agents_runner_run_success(monkeypatch: pytest.MonkeyPatch) -> None:
    """`_agent()` should call `agents.Runner.run(agent, query)`, not `agent.run(query)`."""
    agents = pytest.importorskip("agents")
    from agent_regress.integrations.openai_agents import openai_agents_runner

    captured: dict[str, Any] = {}

    class _FakeResult:
        final_output = "hello from agent"

    async def _fake_run(starting_agent: Any, input: Any, **kwargs: Any) -> _FakeResult:
        captured["starting_agent"] = starting_agent
        captured["input"] = input
        captured.update(kwargs)
        return _FakeResult()

    monkeypatch.setattr(agents.Runner, "run", _fake_run)

    agent = agents.Agent(name="test-agent", instructions="be helpful")
    runner = openai_agents_runner(agent)
    result = runner({"query": "what is 2+2?"})

    assert result == "hello from agent"
    assert captured["starting_agent"] is agent
    assert captured["input"] == "what is 2+2?"
    # Default behavior: no session passed through unless explicitly configured.
    assert captured["session"] is None


@pytest.mark.integration
def test_openai_agents_runner_falls_back_to_str_test_case(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    agents = pytest.importorskip("agents")
    from agent_regress.integrations.openai_agents import openai_agents_runner

    captured: dict[str, Any] = {}

    class _FakeResult:
        final_output = "ok"

    async def _fake_run(starting_agent: Any, input: Any, **kwargs: Any) -> _FakeResult:
        captured["input"] = input
        return _FakeResult()

    monkeypatch.setattr(agents.Runner, "run", _fake_run)

    agent = agents.Agent(name="test-agent", instructions="be helpful")
    runner = openai_agents_runner(agent)
    test_case = {"no_query_key": "value"}
    runner(test_case)

    assert captured["input"] == str(test_case)


@pytest.mark.integration
def test_openai_agents_runner_capture_trace_returns_traced_result(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    agents = pytest.importorskip("agents")
    from agent_regress.integrations.openai_agents import (
        TracedResult,
        openai_agents_runner,
    )

    class _FakeResult:
        final_output = "traced output"

    async def _fake_run(starting_agent: Any, input: Any, **kwargs: Any) -> _FakeResult:
        return _FakeResult()

    monkeypatch.setattr(agents.Runner, "run", _fake_run)

    agent = agents.Agent(name="trace-agent", instructions="be helpful")
    runner = openai_agents_runner(agent, capture_trace=True)
    result = runner({"query": "trace me"})

    assert isinstance(result, TracedResult)
    assert result.output == "traced output"
    assert result.trace is not None
    assert "run_config" in result.trace
    assert "tool_calls" in result.trace
    assert isinstance(result.trace["tool_calls"], list)
    assert isinstance(result.trace["run_config"], dict)


@pytest.mark.integration
def test_openai_agents_runner_capture_trace_false_is_unchanged(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """capture_trace=False (default) must return the raw output, never a TracedResult."""
    agents = pytest.importorskip("agents")
    from agent_regress.integrations.openai_agents import (
        TracedResult,
        openai_agents_runner,
    )

    class _FakeResult:
        final_output = "plain output"

    async def _fake_run(starting_agent: Any, input: Any, **kwargs: Any) -> _FakeResult:
        return _FakeResult()

    monkeypatch.setattr(agents.Runner, "run", _fake_run)

    agent = agents.Agent(name="plain-agent", instructions="be helpful")
    runner = openai_agents_runner(agent)
    result = runner({"query": "plain"})

    assert result == "plain output"
    assert not isinstance(result, TracedResult)


@pytest.mark.integration
def test_openai_agents_runner_session_passthrough(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    agents = pytest.importorskip("agents")
    from agent_regress.integrations.openai_agents import openai_agents_runner

    class _FakeSession:
        pass

    fake_session = _FakeSession()
    captured: dict[str, Any] = {}

    class _FakeResult:
        final_output = "ok"

    async def _fake_run(starting_agent: Any, input: Any, **kwargs: Any) -> _FakeResult:
        captured.update(kwargs)
        return _FakeResult()

    monkeypatch.setattr(agents.Runner, "run", _fake_run)

    agent = agents.Agent(name="session-agent", instructions="be helpful")
    runner = openai_agents_runner(agent, session=fake_session)
    runner({"query": "hi"})

    assert captured["session"] is fake_session


@pytest.mark.integration
def test_openai_agents_runner_session_factory_passthrough(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    agents = pytest.importorskip("agents")
    from agent_regress.integrations.openai_agents import openai_agents_runner

    class _FakeSession:
        pass

    fake_session = _FakeSession()
    factory_calls: list[int] = []

    def _factory() -> _FakeSession:
        factory_calls.append(1)
        return fake_session

    captured: dict[str, Any] = {}

    class _FakeResult:
        final_output = "ok"

    async def _fake_run(starting_agent: Any, input: Any, **kwargs: Any) -> _FakeResult:
        captured.update(kwargs)
        return _FakeResult()

    monkeypatch.setattr(agents.Runner, "run", _fake_run)

    agent = agents.Agent(name="session-factory-agent", instructions="be helpful")
    runner = openai_agents_runner(agent, session_factory=_factory)
    runner({"query": "hi"})

    assert captured["session"] is fake_session
    assert len(factory_calls) == 1


def test_openai_agents_runner_session_aware_reuses_session_per_test_case(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """`session_aware=True` builds one session per logical test case (id-keyed)."""
    agents = pytest.importorskip("agents")
    from agent_regress.integrations.openai_agents import openai_agents_runner

    factory_calls: list[object] = []

    def _factory() -> object:
        session = object()
        factory_calls.append(session)
        return session

    captured_sessions: list[Any] = []

    class _FakeResult:
        final_output = "ok"

    async def _fake_run(starting_agent: Any, input: Any, **kwargs: Any) -> _FakeResult:
        captured_sessions.append(kwargs["session"])
        return _FakeResult()

    monkeypatch.setattr(agents.Runner, "run", _fake_run)

    agent = agents.Agent(name="session-aware-agent", instructions="be helpful")
    runner = openai_agents_runner(agent, session_factory=_factory, session_aware=True)

    test_case_a = {"query": "hi"}
    test_case_b = {"query": "bye"}

    runner(test_case_a)
    runner(test_case_a)  # same test case object -> same session reused
    runner(test_case_b)  # different test case object -> a fresh session

    assert len(factory_calls) == 2  # one per distinct test case, not per call
    assert captured_sessions[0] is captured_sessions[1]
    assert captured_sessions[2] is not captured_sessions[0]


def test_openai_agents_runner_session_aware_false_is_fresh_every_call(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Default `session_aware=False` preserves the original per-call-fresh behavior."""
    agents = pytest.importorskip("agents")
    from agent_regress.integrations.openai_agents import openai_agents_runner

    factory_calls: list[object] = []

    def _factory() -> object:
        session = object()
        factory_calls.append(session)
        return session

    captured_sessions: list[Any] = []

    class _FakeResult:
        final_output = "ok"

    async def _fake_run(starting_agent: Any, input: Any, **kwargs: Any) -> _FakeResult:
        captured_sessions.append(kwargs["session"])
        return _FakeResult()

    monkeypatch.setattr(agents.Runner, "run", _fake_run)

    agent = agents.Agent(name="session-not-aware-agent", instructions="be helpful")
    runner = openai_agents_runner(agent, session_factory=_factory)

    test_case = {"query": "hi"}
    runner(test_case)
    runner(test_case)

    assert len(factory_calls) == 2
    assert captured_sessions[0] is not captured_sessions[1]


def test_openai_agents_runner_session_aware_ignores_explicit_session(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """`session=` (an already-built session) is unaffected by `session_aware=`."""
    agents = pytest.importorskip("agents")
    from agent_regress.integrations.openai_agents import openai_agents_runner

    class _FakeSession:
        pass

    fake_session = _FakeSession()
    captured: dict[str, Any] = {}

    class _FakeResult:
        final_output = "ok"

    async def _fake_run(starting_agent: Any, input: Any, **kwargs: Any) -> _FakeResult:
        captured.update(kwargs)
        return _FakeResult()

    monkeypatch.setattr(agents.Runner, "run", _fake_run)

    agent = agents.Agent(name="explicit-session-agent", instructions="be helpful")
    runner = openai_agents_runner(agent, session=fake_session, session_aware=True)
    runner({"query": "hi"})

    assert captured["session"] is fake_session


def test_openai_agents_runner_capture_trace_records_nested_run_config_inheritance(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """`trace["nested_run_configs"]` flags a nested `Runner.run` that reused the
    exact same top-level `RunConfig` object — the PR #2463 inheritance signal.
    """
    agents = pytest.importorskip("agents")
    from agent_regress.integrations.openai_agents import openai_agents_runner

    nested_agent = agents.Agent(name="nested-tool-agent", instructions="be helpful")
    depth = {"n": 0}

    class _FakeResult:
        final_output = "top-level output"

    async def _fake_run(*args: Any, **kwargs: Any) -> _FakeResult:
        depth["n"] += 1
        if depth["n"] == 1:
            # Simulate the SDK's `Agent.as_tool()` nested dispatch reusing the
            # parent's RunConfig object unchanged (no explicit override) —
            # exactly what agents/agent.py's `_run_agent_impl` does when
            # `as_tool(run_config=...)` was not given an override.
            await agents.Runner.run(
                starting_agent=nested_agent,
                input="nested query",
                run_config=kwargs.get("run_config"),
            )
        return _FakeResult()

    monkeypatch.setattr(agents.Runner, "run", _fake_run)

    agent = agents.Agent(name="top-level-agent", instructions="be helpful")
    runner = openai_agents_runner(agent, capture_trace=True)
    result = runner({"query": "trigger nested tool call"})

    nested = result.trace["nested_run_configs"]
    assert len(nested) == 1
    assert nested[0]["agent_name"] == "nested-tool-agent"
    assert nested[0]["same_object_as_top_level_run_config"] is True


def test_openai_agents_runner_capture_trace_flags_nested_run_config_override(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A nested call with a DIFFERENT RunConfig object is flagged as not-inherited."""
    agents = pytest.importorskip("agents")
    from agent_regress.integrations.openai_agents import openai_agents_runner

    nested_agent = agents.Agent(name="overridden-tool-agent", instructions="be helpful")
    depth = {"n": 0}

    class _FakeResult:
        final_output = "top-level output"

    async def _fake_run(*args: Any, **kwargs: Any) -> _FakeResult:
        depth["n"] += 1
        if depth["n"] == 1:
            # Simulate `as_tool(run_config=<explicit override>)`: a brand-new
            # RunConfig object, not the parent's.
            await agents.Runner.run(
                starting_agent=nested_agent,
                input="nested query",
                run_config=agents.RunConfig(),
            )
        return _FakeResult()

    monkeypatch.setattr(agents.Runner, "run", _fake_run)

    agent = agents.Agent(name="top-level-agent-2", instructions="be helpful")
    runner = openai_agents_runner(agent, capture_trace=True)
    result = runner({"query": "trigger nested tool call with override"})

    nested = result.trace["nested_run_configs"]
    assert len(nested) == 1
    assert nested[0]["same_object_as_top_level_run_config"] is False


def _make_multimodal_function_call_output() -> list[dict[str, Any]]:
    return [
        {
            "type": "function_call_output",
            "call_id": "call_1",
            "output": [
                {"type": "input_text", "text": "here is the result"},
                {"type": "input_image", "image_url": "https://example.com/img.png"},
            ],
        }
    ]


def test_openai_agents_runner_capture_trace_records_converted_tool_outputs(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """`trace["converted_tool_outputs"]` shows whether non-text tool output
    (e.g. an image) survives `Converter.items_to_messages` conversion — the
    PR #2214 concern, downstream of `FunctionSpanData.export()`'s stringification.

    With `preserve_tool_output_all_content=True` (the flag PR #2214-shaped fixes
    plumb through), the image content part survives conversion.
    """
    agents = pytest.importorskip("agents")
    from agent_regress.integrations.openai_agents import openai_agents_runner

    class _FakeResult:
        final_output = "ok"

    async def _fake_run(*args: Any, **kwargs: Any) -> _FakeResult:
        from agents.models.chatcmpl_converter import Converter

        Converter.items_to_messages(
            _make_multimodal_function_call_output(),
            model="gpt-4o",
            preserve_tool_output_all_content=True,
        )
        return _FakeResult()

    monkeypatch.setattr(agents.Runner, "run", _fake_run)

    agent = agents.Agent(name="multimodal-tool-agent", instructions="be helpful")
    runner = openai_agents_runner(agent, capture_trace=True)
    result = runner({"query": "call the multimodal tool"})

    converted = result.trace["converted_tool_outputs"]
    assert len(converted) == 1
    pre = converted[0]["pre_conversion_outputs"]
    assert pre == [
        {
            "call_id": "call_1",
            "output": [
                {"type": "input_text", "text": "here is the result"},
                {"type": "input_image", "image_url": "https://example.com/img.png"},
            ],
        }
    ]
    post = converted[0]["post_conversion_tool_messages"]
    assert len(post) == 1
    assert post[0]["tool_call_id"] == "call_1"
    content_types = {part["type"] for part in post[0]["content"]}
    assert content_types == {"text", "image_url"}


def test_openai_agents_runner_capture_trace_shows_non_text_dropped_without_preserve_flag(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Without `preserve_tool_output_all_content=True` (the default), the SDK's
    converter drops non-text tool output content — exactly the gap PR #2214
    concerns itself with. This is the "converter stripped it" side of the same
    signal the previous test's "converter preserved it" case exercises.
    """
    agents = pytest.importorskip("agents")
    from agent_regress.integrations.openai_agents import openai_agents_runner

    class _FakeResult:
        final_output = "ok"

    async def _fake_run(*args: Any, **kwargs: Any) -> _FakeResult:
        from agents.models.chatcmpl_converter import Converter

        Converter.items_to_messages(
            _make_multimodal_function_call_output(),
            model="gpt-4o",
        )
        return _FakeResult()

    monkeypatch.setattr(agents.Runner, "run", _fake_run)

    agent = agents.Agent(name="multimodal-tool-agent-2", instructions="be helpful")
    runner = openai_agents_runner(agent, capture_trace=True)
    result = runner({"query": "call the multimodal tool"})

    post = result.trace["converted_tool_outputs"][0]["post_conversion_tool_messages"]
    content_types = {part["type"] for part in post[0]["content"]}
    assert content_types == {"text"}
    assert "image_url" not in content_types


def test_openai_agents_runner_capture_trace_converted_tool_outputs_empty_by_default(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """No converter activity during the run -> an empty (not missing) list."""
    agents = pytest.importorskip("agents")
    from agent_regress.integrations.openai_agents import openai_agents_runner

    class _FakeResult:
        final_output = "ok"

    async def _fake_run(*args: Any, **kwargs: Any) -> _FakeResult:
        return _FakeResult()

    monkeypatch.setattr(agents.Runner, "run", _fake_run)

    agent = agents.Agent(name="plain-tool-agent", instructions="be helpful")
    runner = openai_agents_runner(agent, capture_trace=True)
    result = runner({"query": "no tools called"})

    assert result.trace["converted_tool_outputs"] == []
    assert result.trace["nested_run_configs"] == []


class _FakeRealtimeToolStartEvent:
    def __init__(self, tool_name: str) -> None:
        self.tool_name = tool_name


class _FakeRealtimeToolEndEvent:
    def __init__(self, tool_name: str) -> None:
        self.tool_name = tool_name


class _FakeRealtimeOtherEvent:
    pass


class _FakeRealtimeSession:
    """Duck-typed test double for `agents.realtime.RealtimeSession`."""

    def __init__(self) -> None:
        self.sent: list[Any] = []
        self.entered = False
        self.exited = False
        self._events: list[Any] = [
            _FakeRealtimeOtherEvent(),
            _FakeRealtimeToolStartEvent("lookup"),
            _FakeRealtimeToolEndEvent("lookup"),
            _FakeRealtimeOtherEvent(),
        ]
        self._iter = iter(self._events)

    async def __aenter__(self) -> _FakeRealtimeSession:
        self.entered = True
        return self

    async def __aexit__(self, *exc_info: Any) -> bool:
        self.exited = True
        return False

    async def send_message(self, message: Any) -> None:
        self.sent.append(message)

    def __aiter__(self) -> _FakeRealtimeSession:
        return self

    async def __anext__(self) -> Any:
        try:
            return next(self._iter)
        except StopIteration:
            raise StopAsyncIteration from None


def test_openai_agents_realtime_runner_collects_tool_events() -> None:
    from agent_regress.integrations.openai_agents import openai_agents_realtime_runner

    session_holder: dict[str, _FakeRealtimeSession] = {}

    def _factory() -> _FakeRealtimeSession:
        session = _FakeRealtimeSession()
        session_holder["session"] = session
        return session

    runner = openai_agents_realtime_runner(_factory, scripted_inputs=["hello", "world"])
    result = runner({})

    assert "events" in result
    events = result["events"]
    assert len(events) == 2
    assert type(events[0]).__name__ == "_FakeRealtimeToolStartEvent"
    assert type(events[1]).__name__ == "_FakeRealtimeToolEndEvent"

    session = session_holder["session"]
    assert session.sent == ["hello", "world"]
    assert session.entered is True
    assert session.exited is True


def test_openai_agents_realtime_runner_respects_max_events() -> None:
    from agent_regress.integrations.openai_agents import openai_agents_realtime_runner

    def _factory() -> _FakeRealtimeSession:
        return _FakeRealtimeSession()

    runner = openai_agents_realtime_runner(
        _factory, scripted_inputs=["hello"], max_events=1
    )
    result = runner({})

    # Only the first event is consumed (a plain "other" event), so no tool events
    # are collected yet.
    assert result["events"] == []
