"""LangChain LCEL chain runner integration."""

from __future__ import annotations

from typing import Any

from agent_regress.core.runner import AgentCallable


def langchain_runner(chain: Any, input_key: str = "input") -> AgentCallable:
    """Wrap a LangChain LCEL Runnable as an agentregress AgentCallable.

    Args:
        chain: A LangChain Runnable (chain, pipeline, or agent) with .invoke().
        input_key: Key used to extract the relevant field from each test case.
                   When the key is absent, the entire test_case dict is passed.

    Returns:
        An AgentCallable suitable for use with compare() or run_suite().
    """
    try:
        from langchain_core.runnables import Runnable  # noqa: PLC0415
    except ImportError as exc:
        raise ImportError(
            "LangChain integration requires langchain-core. "
            "Install with: pip install agent-regress[langchain]"
        ) from exc

    if not isinstance(chain, Runnable):
        raise TypeError(
            f"chain must be a LangChain Runnable, got {type(chain).__name__}"
        )

    def _agent(test_case: dict[str, Any]) -> Any:
        return chain.invoke({input_key: test_case.get(input_key, test_case)})

    return _agent
