"""OpenAI Agents SDK runner integration."""
from __future__ import annotations

import asyncio
from typing import Any


def openai_agents_runner(agent: Any) -> Any:
    try:
        import openai  # noqa: F401  # type: ignore[import-untyped]
    except ImportError as exc:
        raise ImportError(
            "OpenAI Agents SDK integration requires openai-agents. "
            "Install with: pip install agent-regress[openai-agents]"
        ) from exc

    def _agent(test_case: dict[str, Any]) -> Any:
        query = test_case.get("query", str(test_case))

        async def _run() -> Any:
            return await agent.run(query)

        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:
                    future = ex.submit(asyncio.run, _run())
                    return future.result()
            return loop.run_until_complete(_run())
        except RuntimeError:
            return asyncio.run(_run())

    return _agent
