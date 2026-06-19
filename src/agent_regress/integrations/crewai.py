"""CrewAI crew runner integration."""
from __future__ import annotations

from typing import Any


def crewai_runner(crew: Any) -> Any:
    try:
        import crewai  # noqa: F401  # type: ignore[import-untyped]
    except ImportError as exc:
        raise ImportError(
            "CrewAI integration requires crewai. "
            "Install with: pip install agent-regress[crewai]"
        ) from exc

    def _agent(test_case: dict[str, Any]) -> Any:
        inputs = test_case if isinstance(test_case, dict) else {"input": test_case}
        return crew.kickoff(inputs=inputs)

    return _agent
