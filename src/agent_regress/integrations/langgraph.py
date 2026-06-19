"""LangGraph graph runner integration."""

from __future__ import annotations

from typing import Any

from agent_regress.core.runner import AgentCallable


def langgraph_runner(graph: Any, input_key: str = "messages") -> AgentCallable:
    """Wrap a LangGraph graph as an agentregress AgentCallable.

    Args:
        graph: A compiled LangGraph graph with an .invoke() method.
        input_key: Key used to pass the test case into the graph state.

    Returns:
        An AgentCallable suitable for use with compare() or run_suite().
    """
    try:
        import langgraph  # noqa: F401, PLC0415  # type: ignore[import-untyped]
    except ImportError as exc:
        raise ImportError(
            "LangGraph integration requires langgraph. "
            "Install with: pip install agent-regress[langgraph]"
        ) from exc

    def _agent(test_case: dict[str, Any]) -> Any:
        state = {input_key: test_case.get(input_key, test_case)}
        return graph.invoke(state)

    return _agent
