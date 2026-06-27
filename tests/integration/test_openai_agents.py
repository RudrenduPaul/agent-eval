"""Integration tests for OpenAI Agents SDK runner.

These tests require a real openai-agents installation and optionally a real
OpenAI API key. Run with: pytest tests/integration/ -m integration
"""

from __future__ import annotations

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
