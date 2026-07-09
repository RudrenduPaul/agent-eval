"""Integration tests for CrewAI runner.

These tests require a real CrewAI installation.
Run with: pytest tests/integration/ -m integration
"""

from __future__ import annotations

import pytest


def _crewai_really_importable() -> bool:
    """True only if `import crewai` succeeds cleanly in this environment.

    Some dev environments have crewai installed but unimportable due to an
    unrelated pydantic/chromadb dependency conflict that raises
    `pydantic.v1.errors.ConfigError` (not `ImportError`) on import. That
    case is neither "crewai is missing" (the ImportError path we want to
    exercise) nor "crewai works" (skip) — treat it as untestable here.
    """
    try:
        import crewai  # noqa: F401  # type: ignore[import-untyped]
    except ImportError:
        return False
    else:
        return True


@pytest.mark.integration
def test_crewai_runner_import_error() -> None:
    try:
        importable = _crewai_really_importable()
    except Exception:
        pytest.skip(
            "crewai is installed but fails to import in this environment "
            "due to an unrelated dependency conflict; skipping the real "
            "import-error path (see tests/unit/integrations for "
            "monkeypatched coverage)."
        )
        return

    if importable:
        pytest.skip("crewai installed, skipping import error test")

    from agent_regress.integrations.crewai import crewai_runner

    with pytest.raises(ImportError, match="crewai"):
        crewai_runner(object())


@pytest.mark.integration
def test_crewai_tool_runner_import_error() -> None:
    try:
        importable = _crewai_really_importable()
    except Exception:
        pytest.skip(
            "crewai is installed but fails to import in this environment "
            "due to an unrelated dependency conflict; skipping the real "
            "import-error path (see tests/unit/integrations for "
            "monkeypatched coverage)."
        )
        return

    if importable:
        pytest.skip("crewai installed, skipping import error test")

    from agent_regress.integrations.crewai import crewai_tool_runner

    with pytest.raises(ImportError, match="crewai"):
        crewai_tool_runner(object())
