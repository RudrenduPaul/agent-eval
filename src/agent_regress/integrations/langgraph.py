"""LangGraph graph runner integration."""

from __future__ import annotations

from typing import Any


def langgraph_runner(graph: Any, input_key: str = "messages") -> Any:
    try:
        import langgraph  # noqa: F401, PLC0415  # type: ignore[import-untyped]
    except ImportError as exc:
        raise ImportError(
            "LangGraph integration requires langgraph. "
            "Install with: pip install agent-regress[langgraph]"
        ) from exc

    def _agent(test_case: dict[str, Any]) -> Any:
        state = {input_key: test_case.get(input_key, test_case)}
        result = graph.invoke(state)
        return result

    return _agent
