"""CrewAI crew runner integration."""

from __future__ import annotations

from typing import Any

from agent_regress.core.runner import AgentCallable


def crewai_runner(crew: Any) -> AgentCallable:
    """Wrap a CrewAI Crew as an agentregress AgentCallable.

    Args:
        crew: A CrewAI Crew instance with a .kickoff(inputs=...) method.

    Returns:
        An AgentCallable suitable for use with compare() or run_suite().
    """
    try:
        import crewai  # noqa: F401, PLC0415  # type: ignore[import-untyped]
    except ImportError as exc:
        raise ImportError(
            "CrewAI integration requires crewai. "
            "Install with: pip install agent-regress[crewai]"
        ) from exc

    def _agent(test_case: dict[str, Any]) -> Any:
        inputs: dict[str, Any] = (
            test_case if isinstance(test_case, dict) else {"input": test_case}
        )
        return crew.kickoff(inputs=inputs)

    return _agent
