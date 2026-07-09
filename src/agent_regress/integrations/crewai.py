"""CrewAI crew runner integration."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from agent_regress.core.runner import AgentCallable


def crewai_runner(
    crew: Any = None,
    crew_factory: Callable[[], Any] | None = None,
    kickoff_kwargs: dict[str, Any] | None = None,
) -> AgentCallable:
    """Wrap a CrewAI Crew as an agent-regress AgentCallable.

    Args:
        crew: A CrewAI Crew instance with a .kickoff(inputs=...) method.
            Exactly one of `crew` or `crew_factory` must be provided.
        crew_factory: A zero-arg callable that constructs and returns a fresh
            Crew instance. When provided, a brand-new Crew is built on every
            invocation of the returned AgentCallable instead of reusing a
            single shared Crew object. Exactly one of `crew` or `crew_factory`
            must be provided.
        kickoff_kwargs: Optional extra keyword arguments forwarded to
            `crew.kickoff(inputs=inputs, **kickoff_kwargs)` on every call.
            Defaults to None, which preserves the original behavior of
            calling `crew.kickoff(inputs=inputs)` with no extra kwargs.

    Returns:
        An AgentCallable suitable for use with compare() or run_suite().

    Raises:
        ImportError: If the crewai package is not installed.
        ValueError: If both or neither of `crew`/`crew_factory` are provided.

    Warning:
        **Shared mutable state hazard.** `run_suite(..., max_workers=None)`
        (the default) runs test cases concurrently across a
        `ThreadPoolExecutor` with an unbounded worker count. When
        `crewai_runner(crew=...)` wraps a single, already-constructed `Crew`
        object, that *same* Crew instance is reused for every concurrent
        test-case invocation. CrewAI's memory/knowledge/RAG stores are
        Crew-level shared, mutable state by design: concurrent reads/writes
        against the same store from parallel test-case executions can
        interleave and corrupt results, violating the independent-sample
        assumption that agent-regress's statistical comparisons (e.g.
        Mann-Whitney/bootstrap) rely on. This can produce noise or spurious
        "regression" signals that are actually just concurrency artifacts,
        not real behavioral differences.

        If your Crew has memory, knowledge, or RAG enabled, do ONE of:
          1. Pass `crew_factory=` instead of `crew=` so a fresh Crew (and
             fresh shared state) is built per invocation, or
          2. Pass `crew=` but call `run_suite(..., max_workers=1)` to
             serialize test-case execution against the shared Crew.
    """
    try:
        import crewai  # noqa: F401, PLC0415  # type: ignore[import-untyped]
    except ImportError as exc:
        raise ImportError(
            "CrewAI integration requires crewai. "
            "Install with: pip install agent-regress[crewai]"
        ) from exc

    if (crew is None) == (crew_factory is None):
        raise ValueError(
            "Exactly one of `crew` or `crew_factory` must be provided to "
            "crewai_runner()."
        )

    def _agent(test_case: dict[str, Any]) -> Any:
        inputs: dict[str, Any] = (
            test_case if isinstance(test_case, dict) else {"input": test_case}
        )
        active_crew = crew_factory() if crew_factory is not None else crew
        return active_crew.kickoff(inputs=inputs, **(kickoff_kwargs or {}))

    return _agent


def crewai_tool_runner(tool: Any) -> AgentCallable:
    """Wrap a single CrewAI tool (BaseTool/CrewStructuredTool) as an AgentCallable.

    Invokes the tool directly via its `run()` method if present, falling back
    to `_run()` otherwise, so a test suite can exercise one tool's behavior
    across N runs without requiring a full multi-step Crew `kickoff()` to
    converge.

    Args:
        tool: A CrewAI `BaseTool`/`CrewStructuredTool` instance (or any
            duck-typed object exposing a `run(**kwargs)` or `_run(**kwargs)`
            method).

    Returns:
        An AgentCallable suitable for use with compare() or run_suite().
        The returned callable's `_agent(test_case)` extracts keyword
        arguments from `test_case["tool_kwargs"]` if present, otherwise uses
        `test_case` itself as the kwargs dict, and returns the tool's raw
        result unmodified.

    Raises:
        ImportError: If the crewai package is not installed.
    """
    try:
        import crewai  # noqa: F401, PLC0415  # type: ignore[import-untyped]
    except ImportError as exc:
        raise ImportError(
            "CrewAI integration requires crewai. "
            "Install with: pip install agent-regress[crewai]"
        ) from exc

    def _agent(test_case: dict[str, Any]) -> Any:
        tool_kwargs: dict[str, Any] = test_case.get("tool_kwargs", test_case)
        run = getattr(tool, "run", None)
        if callable(run):
            return run(**tool_kwargs)
        return tool._run(**tool_kwargs)

    return _agent
