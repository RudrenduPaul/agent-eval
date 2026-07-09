"""Unit tests for the CrewAI integration using duck-typed fakes.

These tests do NOT require a real crewai installation. They monkeypatch
sys.modules["crewai"] so the internal `import crewai` guard succeeds, then
exercise the wrapper logic against small duck-typed fake Crew/tool objects.
"""

from __future__ import annotations

import sys
from typing import Any
from unittest.mock import MagicMock

import pytest

from agent_regress.integrations.crewai import crewai_runner, crewai_tool_runner


@pytest.fixture(autouse=True)
def _fake_crewai_module(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setitem(sys.modules, "crewai", MagicMock())


class FakeCrew:
    """Duck-typed fake Crew with a .kickoff(inputs=...) method."""

    def __init__(self, crew_id: str = "default") -> None:
        self.crew_id = crew_id
        self.kickoff_calls: list[tuple[dict[str, Any], dict[str, Any]]] = []

    def kickoff(self, inputs: dict[str, Any], **kwargs: Any) -> dict[str, Any]:
        self.kickoff_calls.append((inputs, kwargs))
        return {"crew_id": self.crew_id, "inputs": inputs, "kwargs": kwargs}


class FakeToolWithRun:
    """Duck-typed fake tool exposing a public run() method."""

    def __init__(self) -> None:
        self.run_calls: list[dict[str, Any]] = []

    def run(self, **kwargs: Any) -> dict[str, Any]:
        self.run_calls.append(kwargs)
        return {"via": "run", **kwargs}

    def _run(self, **kwargs: Any) -> dict[str, Any]:  # pragma: no cover
        raise AssertionError("_run() should not be called when run() exists")


class FakeToolPrivateOnly:
    """Duck-typed fake tool exposing only the private _run() method."""

    def __init__(self) -> None:
        self.run_calls: list[dict[str, Any]] = []

    def _run(self, **kwargs: Any) -> dict[str, Any]:
        self.run_calls.append(kwargs)
        return {"via": "_run", **kwargs}


class TestCrewaiToolRunner:
    def test_uses_public_run_when_present(self) -> None:
        tool = FakeToolWithRun()
        agent = crewai_tool_runner(tool)
        result = agent({"tool_kwargs": {"query": "hello"}})
        assert result == {"via": "run", "query": "hello"}
        assert tool.run_calls == [{"query": "hello"}]

    def test_falls_back_to_private_run(self) -> None:
        tool = FakeToolPrivateOnly()
        agent = crewai_tool_runner(tool)
        result = agent({"tool_kwargs": {"query": "hi"}})
        assert result == {"via": "_run", "query": "hi"}
        assert tool.run_calls == [{"query": "hi"}]

    def test_extracts_tool_kwargs_key_when_present(self) -> None:
        tool = FakeToolWithRun()
        agent = crewai_tool_runner(tool)
        agent({"tool_kwargs": {"a": 1}, "expected": "unused"})
        assert tool.run_calls == [{"a": 1}]

    def test_uses_full_test_case_when_no_tool_kwargs_key(self) -> None:
        tool = FakeToolWithRun()
        agent = crewai_tool_runner(tool)
        agent({"a": 1, "b": 2})
        assert tool.run_calls == [{"a": 1, "b": 2}]

    def test_returns_raw_tool_result_unmodified(self) -> None:
        tool = FakeToolWithRun()
        agent = crewai_tool_runner(tool)
        result = agent({"tool_kwargs": {"x": "y"}})
        assert result == {"via": "run", "x": "y"}


class TestCrewaiRunnerKickoffKwargsPassthrough:
    def test_default_none_preserves_original_behavior(self) -> None:
        crew = FakeCrew()
        agent = crewai_runner(crew)
        agent({"query": "hi"})
        inputs, kwargs = crew.kickoff_calls[0]
        assert inputs == {"query": "hi"}
        assert kwargs == {}

    def test_forwards_extra_kickoff_kwargs(self) -> None:
        crew = FakeCrew()
        agent = crewai_runner(crew, kickoff_kwargs={"restore_from_state_id": "abc123"})
        agent({"query": "hi"})
        _, kwargs = crew.kickoff_calls[0]
        assert kwargs == {"restore_from_state_id": "abc123"}

    def test_non_dict_test_case_wrapped_as_input(self) -> None:
        crew = FakeCrew()
        agent = crewai_runner(crew)
        agent("raw string case")  # type: ignore[arg-type]
        inputs, _ = crew.kickoff_calls[0]
        assert inputs == {"input": "raw string case"}


class TestCrewaiRunnerCrewFactory:
    def test_crew_factory_builds_fresh_crew_per_invocation(self) -> None:
        built: list[FakeCrew] = []

        def factory() -> FakeCrew:
            crew = FakeCrew(crew_id=f"crew-{len(built)}")
            built.append(crew)
            return crew

        agent = crewai_runner(crew_factory=factory)
        result_a = agent({"query": "one"})
        result_b = agent({"query": "two"})

        assert len(built) == 2
        assert built[0] is not built[1]
        assert result_a["crew_id"] == "crew-0"
        assert result_b["crew_id"] == "crew-1"

    def test_crew_factory_respects_kickoff_kwargs(self) -> None:
        built: list[FakeCrew] = []

        def factory() -> FakeCrew:
            crew = FakeCrew()
            built.append(crew)
            return crew

        agent = crewai_runner(crew_factory=factory, kickoff_kwargs={"foo": "bar"})
        agent({"query": "one"})
        _, kwargs = built[0].kickoff_calls[0]
        assert kwargs == {"foo": "bar"}

    def test_both_crew_and_crew_factory_raises_value_error(self) -> None:
        with pytest.raises(ValueError, match="Exactly one"):
            crewai_runner(crew=FakeCrew(), crew_factory=FakeCrew)

    def test_neither_crew_nor_crew_factory_raises_value_error(self) -> None:
        with pytest.raises(ValueError, match="Exactly one"):
            crewai_runner()


class TestCrewaiRunnerBackwardCompatibility:
    def test_positional_crew_arg_still_works(self) -> None:
        crew = FakeCrew()
        agent = crewai_runner(crew)
        result = agent({"query": "hi"})
        assert result["inputs"] == {"query": "hi"}
        assert result["kwargs"] == {}
