"""OpenAI Agents SDK runner integration."""

from __future__ import annotations

import asyncio
import concurrent.futures
from typing import Any

from agent_regress.core.runner import AgentCallable


def openai_agents_runner(agent: Any) -> AgentCallable:
    """Wrap an OpenAI Agents SDK agent as an agent-regress AgentCallable.

    Handles both synchronous and async (Jupyter / already-running-loop) contexts
    by spawning a background thread when a running event loop is detected.

    Args:
        agent: An OpenAI Agents SDK agent with an async .run(query) method.

    Returns:
        An AgentCallable suitable for use with compare() or run_suite().
    """
    try:
        import agents  # noqa: F401, PLC0415  # type: ignore[import-untyped]
    except ImportError as exc:
        raise ImportError(
            "OpenAI Agents SDK integration requires openai-agents. "
            "Install with: pip install agent-regress[openai-agents]"
        ) from exc

    async def _run(query: str) -> Any:
        return await agent.run(query)

    def _agent(test_case: dict[str, Any]) -> Any:
        query = test_case.get("query", str(test_case))
        try:
            asyncio.get_running_loop()
            loop_running = True
        except RuntimeError:
            loop_running = False

        if loop_running:
            # A loop is already running (e.g. Jupyter) — run in a fresh thread.
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:
                return ex.submit(asyncio.run, _run(query)).result()
        else:
            return asyncio.run(_run(query))

    return _agent
