"""LangChain LCEL chain runner integration."""
from __future__ import annotations

from typing import Any


def langchain_runner(chain: Any, input_key: str = "input") -> Any:
    try:
        from langchain_core.runnables import Runnable  # type: ignore[import-untyped]
    except ImportError as exc:
        raise ImportError(
            "LangChain integration requires langchain-core. "
            "Install with: pip install agent-regress[langchain]"
        ) from exc

    if not isinstance(chain, Runnable):
        raise TypeError(f"chain must be a LangChain Runnable, got {type(chain).__name__}")

    def _agent(test_case: dict[str, Any]) -> Any:
        return chain.invoke({input_key: test_case.get(input_key, test_case)})

    return _agent
