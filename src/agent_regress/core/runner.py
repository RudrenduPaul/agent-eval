"""Runs an agent callable N times on a fixed test suite."""

from __future__ import annotations

import asyncio
import concurrent.futures
import json
import subprocess
import warnings
from collections.abc import Awaitable, Callable
from typing import Any

_MIN_STATISTICAL_N = 10
_MIN_RELIABLE_N = 30
_NEAR_ZERO_VARIANCE_TOLERANCE = 1e-9

CACHE_BUST_NONCE_KEY = "_cache_bust_nonce"
"""Reserved key name a `cache_bust_key_fn` should inject its nonce under.

`run_suite(cache_bust_key_fn=...)` merges whatever dict `cache_bust_key_fn`
returns into the test case before calling `agent(...)` (see `run_suite`'s
docstring). Downstream integrations that narrow a test case down to a
framework-specific input shape (e.g.
`agent_regress.integrations.langgraph._build_state()`, which projects the
test case down to a single `input_key` such as `"messages"`) need a single,
predictable key name to preserve through that narrowing so the cache-bust
nonce survives. Injecting the nonce under `CACHE_BUST_NONCE_KEY` (rather
than an arbitrary key of the caller's choosing) is what lets integration
code special-case exactly one key and still guarantee the nonce reaches the
system under test, regardless of which top-level keys get dropped
otherwise.
"""

AgentCallable = Callable[[dict[str, Any]], Any]
AsyncAgentCallable = Callable[[dict[str, Any]], Awaitable[Any]]
ScorerCallable = Callable[[Any, dict[str, Any]], float]


CacheBustKeyFn = Callable[[dict[str, Any], int], dict[str, Any]]


def _to_score(
    raw: Any, test_case: dict[str, Any], scorer: ScorerCallable | None
) -> float:
    """Convert a raw agent output into a float score.

    Shared by `run_suite()` and `arun_suite()` so the scoring contract (use
    `scorer()` if given, otherwise require a numeric return value) lives in
    exactly one place.
    """
    if scorer is not None:
        return float(scorer(raw, test_case))
    if isinstance(raw, (int, float)):
        return float(raw)
    raise TypeError(
        f"Agent returned {type(raw).__name__!r}. "
        "Either return a float directly or pass "
        "scorer= to convert output to float."
    )


def _clamp_score(score: float) -> float:
    """Clamp a score into [0.0, 1.0], warning if it was out of range.

    Shared by `run_suite()` and `arun_suite()`.
    """
    if not (0.0 <= score <= 1.0):
        warnings.warn(
            f"Score {score:.4f} outside [0.0, 1.0]. Clamping. "
            "Ensure your scorer returns values in [0.0, 1.0].",
            UserWarning,
            stacklevel=3,
        )
        return max(0.0, min(1.0, score))
    return score


def run_suite(  # noqa: PLR0913
    agent: AgentCallable,
    test_suite: list[dict[str, Any]],
    n_runs: int = 50,
    scorer: ScorerCallable | None = None,
    max_workers: int | None = None,
    stateful: bool = False,
    cache_bust_key_fn: CacheBustKeyFn | None = None,
) -> list[float]:
    """Run `agent` against `test_suite` `n_runs` times per test case.

    Args:
        agent: Callable under test. Receives a single test-case dict per call.
        test_suite: List of test-case dicts.
        n_runs: Number of repeated calls per test case.
        scorer: Optional callable converting the agent's raw output to a float
            score. If omitted, the agent's output must already be numeric.
        max_workers: Max worker threads for the ThreadPoolExecutor running
            test cases concurrently. Each test case's own `n_runs` loop
            always executes sequentially within a single worker.
        stateful: Documents (rather than switches) the shared,
            framework-agnostic state contract `run_suite` guarantees by
            construction: test cases are parallelized across the
            `ThreadPoolExecutor`, but a single test case's `n_runs` repeated
            calls to `agent` are always run sequentially, one after another,
            on one worker thread — never interleaved with each other and
            never interleaved with another test case's repeated calls. Any
            `agent` closure that accumulates cross-call state (e.g.
            `agent_regress.integrations.langgraph.langgraph_runner(...,
            thread_aware=True)`'s per-test-case `thread_id`/checkpointer
            continuity, or an OpenAI Agents SDK session-continuity wrapper in
            a separate integration) relies on exactly this guarantee to be
            safe to use with `run_suite`. Set `stateful=True` at the call
            site to make that reliance explicit for readers; because the
            guarantee already holds unconditionally, `stateful=True` and the
            default `stateful=False` produce byte-for-byte identical
            execution and output.
        cache_bust_key_fn: Optional callable `(test_case, run_index) -> dict`.
            When provided, before each of the `n_runs` calls for a test case,
            `run_suite` builds `augmented_case = {**test_case,
            **cache_bust_key_fn(test_case, run_index)}` and passes that to
            `agent(...)` instead of the raw `test_case`. Use this to inject a
            per-run nonce field that a wrapped agent can thread through to
            the underlying system under test to defeat SUT-side caching
            (e.g. LangGraph node/task `cache_policy`), which would otherwise
            silently collapse repeated-sampling variance. Inject the nonce
            under the reserved `CACHE_BUST_NONCE_KEY` constant (exported
            from this module) rather than an arbitrary key name, e.g.:

                import uuid
                from agent_regress.core.runner import (
                    CACHE_BUST_NONCE_KEY,
                    run_suite,
                )

                run_suite(
                    agent,
                    test_suite,
                    cache_bust_key_fn=lambda tc, i: {
                        CACHE_BUST_NONCE_KEY: str(uuid.uuid4())
                    },
                )

            Integrations that narrow a test case down to a framework-specific
            input shape (e.g. `agent_regress.integrations.langgraph`'s state
            builder, which projects the test case down to a single input
            key) special-case `CACHE_BUST_NONCE_KEY` to preserve it through
            that narrowing, so the nonce still reaches the system under
            test. Defaults to `None`, which preserves current behavior
            exactly: the agent always receives the raw `test_case`.

    Returns:
        Flat list of scores across all test cases and all runs.
    """
    if not callable(agent):
        raise TypeError("agent must be callable")
    if not test_suite:
        raise ValueError("test_suite must not be empty")
    if n_runs < 1:
        raise ValueError(f"n_runs must be >= 1, got {n_runs}")

    if n_runs < _MIN_RELIABLE_N:
        warnings.warn(
            f"n_runs={n_runs} is below the minimum for statistical validity "
            f"({_MIN_STATISTICAL_N}). "
            f"Use at least {_MIN_RELIABLE_N} runs per version for reliable results.",
            UserWarning,
            stacklevel=2,
        )

    def _run_case(test_case: dict[str, Any]) -> list[float]:
        case_scores: list[float] = []
        for run_index in range(n_runs):
            if cache_bust_key_fn is not None:
                augmented_case = {
                    **test_case,
                    **cache_bust_key_fn(test_case, run_index),
                }
            else:
                augmented_case = test_case
            score = _clamp_score(_to_score(agent(augmented_case), test_case, scorer))
            case_scores.append(score)
        return case_scores

    all_scores: list[float] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = [pool.submit(_run_case, tc) for tc in test_suite]
        for fut in concurrent.futures.as_completed(futures):
            all_scores.extend(fut.result())

    score_range = max(all_scores) - min(all_scores)
    if score_range < _NEAR_ZERO_VARIANCE_TOLERANCE and n_runs >= _MIN_STATISTICAL_N:
        warnings.warn(
            "All scores returned by run_suite() are identical (or "
            "near-identical, within floating-point noise) across every "
            f"test case and all n_runs={n_runs} runs. This is statistically "
            "implausible unless the system under test is fully deterministic "
            "and cached. Check for SUT-side caching (e.g. LangGraph node/task "
            "cache_policy) and consider passing cache_bust_key_fn= to "
            "run_suite() to inject a per-run nonce that defeats it.",
            UserWarning,
            stacklevel=2,
        )

    return all_scores


async def arun_suite(  # noqa: PLR0913
    agent: AsyncAgentCallable,
    test_suite: list[dict[str, Any]],
    n_runs: int = 50,
    scorer: ScorerCallable | None = None,
    max_concurrency: int | None = None,
    stateful: bool = False,
) -> list[float]:
    """Async counterpart to `run_suite()`.

    Runs `agent` (an `async def`/awaitable callable) against `test_suite`
    `n_runs` times per test case, using `asyncio.gather` instead of a
    `ThreadPoolExecutor`. This exists because `run_suite`/`compare()`'s
    synchronous, independent-sample-per-call model structurally cannot
    reach bugs that only manifest under a sustained async event loop (e.g.
    a queue that gets poisoned by a cancelled future while other callers are
    still waiting on it) — `arun_suite` is what lets such an `agent` be
    driven at all, and `concurrent_cancellation_probe` (below) is the
    purpose-built harness for that specific class of bug.

    Args:
        agent: Async callable under test (`async def agent(test_case) -> Any`
            or any callable returning an awaitable). Receives a single
            test-case dict per call.
        test_suite: List of test-case dicts.
        n_runs: Number of repeated calls per test case.
        scorer: Optional callable converting the agent's raw output to a
            float score. If omitted, the agent's output must already be
            numeric. Uses the exact same scoring contract as `run_suite`
            (both call the shared `_to_score` helper).
        max_concurrency: Optional cap on the number of `agent` calls allowed
            to be in flight at once, enforced with an `asyncio.Semaphore`.
            The cap applies across *all* calls — every test case's every
            run — not per test case. `None` (the default) means unbounded
            concurrency, i.e. every call is scheduled via `asyncio.gather`
            with no semaphore gating.
        stateful: When `True`, mirrors `run_suite(..., stateful=True)`'s
            per-test-case sequencing guarantee: the `n_runs` calls for one
            test case are awaited one after another (never interleaved with
            each other), while different test cases still run concurrently
            with each other (bounded by `max_concurrency` if given). Unlike
            `run_suite` — where sequential-per-case execution already holds
            unconditionally because of the thread-per-case design, making
            `stateful` a documentation-only flag — `arun_suite`'s default
            (`stateful=False`) genuinely interleaves a test case's own
            repeated calls with everything else via a single flat
            `asyncio.gather`, so `stateful=True` here changes real
            scheduling behavior, not just documentation. Set this to `True`
            whenever `agent` is a closure that accumulates cross-call state
            for a given test case (e.g. a thread/session-aware async
            LangGraph runner).

    Returns:
        Flat list of scores across all test cases and all runs.
    """
    if not callable(agent):
        raise TypeError("agent must be callable")
    if not test_suite:
        raise ValueError("test_suite must not be empty")
    if n_runs < 1:
        raise ValueError(f"n_runs must be >= 1, got {n_runs}")
    if max_concurrency is not None and max_concurrency < 1:
        raise ValueError(f"max_concurrency must be >= 1, got {max_concurrency}")

    if n_runs < _MIN_RELIABLE_N:
        warnings.warn(
            f"n_runs={n_runs} is below the minimum for statistical validity "
            f"({_MIN_STATISTICAL_N}). "
            f"Use at least {_MIN_RELIABLE_N} runs per version for reliable results.",
            UserWarning,
            stacklevel=2,
        )

    semaphore = (
        asyncio.Semaphore(max_concurrency) if max_concurrency is not None else None
    )

    async def _call(test_case: dict[str, Any]) -> float:
        if semaphore is not None:
            async with semaphore:
                raw = await agent(test_case)
        else:
            raw = await agent(test_case)
        return _clamp_score(_to_score(raw, test_case, scorer))

    async def _run_case_sequential(test_case: dict[str, Any]) -> list[float]:
        case_scores: list[float] = []
        for _ in range(n_runs):
            case_scores.append(await _call(test_case))
        return case_scores

    async def _run_case_gathered(test_case: dict[str, Any]) -> list[float]:
        return list(await asyncio.gather(*(_call(test_case) for _ in range(n_runs))))

    run_case = _run_case_sequential if stateful else _run_case_gathered

    per_case_results = await asyncio.gather(*(run_case(tc) for tc in test_suite))

    all_scores: list[float] = []
    for case_scores in per_case_results:
        all_scores.extend(case_scores)

    score_range = max(all_scores) - min(all_scores)
    if score_range < _NEAR_ZERO_VARIANCE_TOLERANCE and n_runs >= _MIN_STATISTICAL_N:
        warnings.warn(
            "All scores returned by arun_suite() are identical across every "
            f"test case and all n_runs={n_runs} runs (or vary by less than "
            "floating-point noise). This is statistically implausible unless "
            "the system under test is fully deterministic and cached.",
            UserWarning,
            stacklevel=2,
        )

    return all_scores


def subprocess_runner(
    python_executable: str, script_path: str, timeout: float | None = None
) -> AgentCallable:
    """Build an `AgentCallable` that dispatches each call to a subprocess.

    This is the reference pattern for cross-environment/cross-version
    comparisons: `compare()`'s `version_a`/`version_b` only need to be
    `AgentCallable`s (`dict -> Any`), so nothing about `compare()` or
    `run_suite()` requires the agent under test to live in the current
    Python interpreter or have the current process's installed package
    versions. `subprocess_runner()` closes that gap by shelling out to a
    *different* Python executable (e.g. the `python` of a venv pinned to
    `crewai==0.60.0`) for every single call, so `version_a` can be backed by
    one installed package version and `version_b` by a completely different
    one -- something impossible to do with two in-process objects sharing
    one `sys.modules`.

    Contract for `script_path`: the target script must read a single JSON
    object (the test case) from stdin, and print a single JSON-serializable
    value to stdout (nothing else -- any extra prints will corrupt the
    `json.loads()` parse). A minimal conforming script:

        import sys, json

        test_case = json.loads(sys.stdin.read())
        # ... build/invoke the pinned-version agent here ...
        result = {"output": ...}
        print(json.dumps(result))

    See `docs/cross-version-comparison.md` for a full worked example,
    including a CrewAI script that imports a pinned `crewai` version from
    its own isolated venv.

    Args:
        python_executable: Path to the Python interpreter to run
            `script_path` with, e.g. `"/path/to/venvA/bin/python"`. Using a
            different interpreter/venv per call is what makes this useful
            for comparing two installed versions of the same package --
            each venv has its own `site-packages`, so `version_a` and
            `version_b` never share an import of the target framework.
        script_path: Path to the script to run. Must conform to the stdin/
            stdout JSON contract documented above.
        timeout: Optional timeout in seconds passed straight through to
            `subprocess.run(..., timeout=timeout)`. `None` (the default)
            means no timeout, matching `subprocess.run`'s own default.

    Returns:
        An `AgentCallable`: calling it with a test-case dict runs
        `[python_executable, script_path]` as a subprocess, feeds the test
        case to it as JSON on stdin, and returns the parsed JSON result read
        back from stdout.

    Raises:
        RuntimeError: If the subprocess exits with a non-zero return code.
            The error message includes the captured stderr for debugging.
        subprocess.TimeoutExpired: If `timeout` is given and exceeded.
        json.JSONDecodeError: If stdout is not valid JSON.
    """

    def _agent(test_case: dict[str, Any]) -> Any:
        result = subprocess.run(  # noqa: S603 -- fixed argv list, shell=True never used
            [python_executable, script_path],
            input=json.dumps(test_case),
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
        if result.returncode != 0:
            raise RuntimeError(
                f"subprocess_runner: {python_executable} {script_path} exited "
                f"with code {result.returncode}. stderr:\n{result.stderr}"
            )
        return json.loads(result.stdout)

    return _agent


def _default_cancel_indices(n_concurrent: int, cancel_fraction: float) -> set[int]:
    """Deterministic default cancellation index set.

    Cancels every `round(1 / cancel_fraction)`-th task by index (0-based),
    e.g. `cancel_fraction=0.3` cancels indices `0, 3, 6, ...`. Never uses
    `random` or wall-clock timing so results are reproducible across runs.
    """
    if cancel_fraction <= 0.0:
        return set()
    step = max(round(1.0 / cancel_fraction), 1)
    return set(range(0, n_concurrent, step))


async def concurrent_cancellation_probe(
    agent: AsyncAgentCallable,
    test_case: dict[str, Any],
    n_concurrent: int,
    cancel_fraction: float = 0.3,
    cancel_indices: set[int] | None = None,
) -> dict[str, int]:
    """Concurrency/cancellation-injection harness for a sustained-process async agent.

    Fires `n_concurrent` concurrent `agent(test_case)` calls as
    `asyncio.Task`s, cancels a `cancel_fraction` of them, then awaits
    everything with `asyncio.gather(..., return_exceptions=True)`. This is a
    throughput/liveness probe, not a scoring function: it exists to reach
    bugs like a shared async batch queue getting permanently poisoned by a
    cancelled future while other concurrent callers are still waiting on it
    (a class of bug `run_suite`/`compare()`'s independent-per-call sampling
    model cannot reach, because it never has multiple calls against the same
    live agent/session in flight with one of them being cancelled
    mid-flight).

    Args:
        agent: Async callable under test.
        test_case: A single test-case dict passed to every concurrent call.
        n_concurrent: Number of concurrent `agent(test_case)` calls to fire.
        cancel_fraction: Fraction (in `[0.0, 1.0]`) of the `n_concurrent`
            tasks to cancel, used only to compute the default
            `cancel_indices` when `cancel_indices` is not given. Ignored if
            `cancel_indices` is given explicitly.
        cancel_indices: Optional explicit, deterministic set of 0-based task
            indices to cancel. Pass this for deterministic tests. When
            omitted (`None`), defaults to cancelling every
            `round(1 / cancel_fraction)`-th task by index — no `random` or
            wall-clock-time-based nondeterminism is used internally.

    Returns:
        `{"completed": N, "cancelled": N, "failed": N}` — counts of tasks
        that finished normally, were cancelled, or raised any other
        exception, across the `n_concurrent` tasks fired.
    """
    if not callable(agent):
        raise TypeError("agent must be callable")
    if n_concurrent < 1:
        raise ValueError(f"n_concurrent must be >= 1, got {n_concurrent}")
    if not (0.0 <= cancel_fraction <= 1.0):
        raise ValueError(
            f"cancel_fraction must be in [0.0, 1.0], got {cancel_fraction}"
        )

    if cancel_indices is None:
        cancel_indices = _default_cancel_indices(n_concurrent, cancel_fraction)

    tasks = [asyncio.ensure_future(agent(test_case)) for _ in range(n_concurrent)]

    # Let every task get a chance to actually start running before cancelling
    # any of them, so cancellation lands mid-flight (the realistic case)
    # rather than pre-empting tasks that never got scheduled at all.
    await asyncio.sleep(0)

    for idx in cancel_indices:
        if 0 <= idx < n_concurrent:
            tasks[idx].cancel()

    results = await asyncio.gather(*tasks, return_exceptions=True)

    completed = 0
    cancelled = 0
    failed = 0
    for result in results:
        if isinstance(result, asyncio.CancelledError):
            cancelled += 1
        elif isinstance(result, BaseException):
            failed += 1
        else:
            completed += 1

    return {"completed": completed, "cancelled": cancelled, "failed": failed}
