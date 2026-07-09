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
def test_openai_agents_runner_session_passthrough(monkeypatch: pytest.MonkeyPatch) -> None:
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
