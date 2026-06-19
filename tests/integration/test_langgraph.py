"""Integration tests for LangGraph runner.

These tests require a real LangGraph installation and optionally a real LLM API key.
Run with: pytest tests/integration/ -m integration
"""

from __future__ import annotations

import pytest


@pytest.mark.integration
def test_langgraph_runner_import_error() -> None:
    try:
        import langgraph  # noqa: F401  # type: ignore[import-untyped]

        pytest.skip("langgraph installed, skipping import error test")
    except ImportError:
        from agent_regress.integrations.langgraph import langgraph_runner

        with pytest.raises(ImportError, match="langgraph"):
            langgraph_runner(object())


@pytest.mark.integration
def test_langchain_runner_import_error() -> None:
    try:
        import langchain_core  # noqa: F401  # type: ignore[import-untyped]

        pytest.skip("langchain_core installed, skipping import error test")
    except ImportError:
        from agent_regress.integrations.langchain import langchain_runner

        with pytest.raises(ImportError, match="langchain"):
            langchain_runner(object())
