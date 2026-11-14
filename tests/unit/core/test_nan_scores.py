"""NaN scores must never become successful evaluations."""

import asyncio

import pytest

from agent_regress.core.runner import arun_suite, run_suite


@pytest.mark.parametrize("custom_scorer", [False, True])
@pytest.mark.parametrize("asynchronous", [False, True])
def test_nan_score_is_rejected(custom_scorer: bool, asynchronous: bool) -> None:
    def agent(test_case: dict[str, object]) -> float:
        return float("nan")

    async def async_agent(test_case: dict[str, object]) -> float:
        return agent(test_case)

    def scorer(output: object, test_case: dict[str, object]) -> float:
        return float("nan")

    with pytest.warns(UserWarning, match="n_runs=1"):
        with pytest.raises(ValueError, match="NaN"):
            if asynchronous:
                asyncio.run(
                    arun_suite(
                        async_agent,
                        [{}],
                        n_runs=1,
                        scorer=scorer if custom_scorer else None,
                    )
                )
            else:
                run_suite(
                    agent,
                    [{}],
                    n_runs=1,
                    scorer=scorer if custom_scorer else None,
                )
