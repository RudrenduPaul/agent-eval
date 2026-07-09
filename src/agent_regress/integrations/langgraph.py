"""LangGraph graph runner integration."""

from __future__ import annotations

import inspect
import itertools
from collections.abc import Awaitable, Callable
from typing import Any

from agent_regress.core.runner import (
    CACHE_BUST_NONCE_KEY,
    AgentCallable,
    AsyncAgentCallable,
)


def _build_state(test_case: dict[str, Any], input_key: str) -> dict[str, Any]:
    """Build the graph input state dict from a test case.

    Shared by `langgraph_runner()` and `langgraph_async_runner()`: if
    `input_key` is present in `test_case`, only that field is passed as the
    graph state; otherwise the entire test case dict is passed through
    unchanged.

    When narrowing to just `input_key`, `CACHE_BUST_NONCE_KEY` (the nonce
    `run_suite(cache_bust_key_fn=...)` injects into each test case, see
    `agent_regress.core.runner`) is preserved alongside it if present.
    Without this, the narrowing branch would silently drop the nonce before
    it ever reached the graph, defeating cache-busting for every LangGraph
    runner whose test cases carry `input_key` (reported by @nfcampos).
    """
    if input_key in test_case:
        state = {input_key: test_case[input_key]}
        if CACHE_BUST_NONCE_KEY in test_case:
            state[CACHE_BUST_NONCE_KEY] = test_case[CACHE_BUST_NONCE_KEY]
        return state
    return test_case


def _wire_store_into_config(
    config: dict[str, Any] | None, store: Any
) -> dict[str, Any] | None:
    """Best-effort store wiring into a LangGraph invoke-time config dict.

    LangGraph does not expose a documented `store=` keyword on
    `.invoke()`/`.ainvoke()` — a compiled graph's store is normally wired in
    at compile time via `graph.compile(store=...)`, not at invoke time. Since
    there is no confirmed runtime-injection kwarg to forward `store` to
    instead, this helper never silently drops it: it stashes `store` under
    `config["configurable"]["store"]`, a location a custom node function can
    read back out via `config["configurable"]["store"]`, or a caller can
    inspect after the fact. If a future LangGraph version adds a genuine
    `.ainvoke(..., store=...)` runtime parameter, forward it there directly
    instead of relying on this passthrough.
    """
    if store is None:
        return config
    merged = dict(config) if config is not None else {}
    configurable = dict(merged.get("configurable", {}))
    configurable.setdefault("store", store)
    merged["configurable"] = configurable
    return merged


def langgraph_runner(  # noqa: PLR0913
    graph: Any,
    input_key: str = "messages",
    config: dict[str, Any] | None = None,
    context: dict[str, Any] | None = None,
    thread_aware: bool = False,
    thread_id_factory: Callable[[], str] | None = None,
    operation: Callable[[Any, dict[str, Any]], Any] | None = None,
) -> AgentCallable:
    """Wrap a LangGraph graph as an agent-regress AgentCallable.

    Args:
        graph: A compiled LangGraph graph with an .invoke() method.
        input_key: Key used to pass the test case into the graph state.
        config: Optional LangGraph ``config`` dict passed through unchanged on
            every call as ``graph.invoke(state, config=config)``. Useful for
            passing ``configurable`` values (model name, tags, etc.) that are
            identical across all test cases/runs. Defaults to ``None``, which
            preserves the original ``graph.invoke(state)``-only call.
        context: Optional LangGraph ``context`` dict, for the newer
            ``context`` API some LangGraph versions expose alongside (and
            eventually in place of) ``config["configurable"]``. Because the
            installed LangGraph version is not known at import time, this
            wrapper inspects ``graph.invoke``'s signature and only forwards
            ``context=`` if the callable actually declares a ``context``
            parameter; otherwise it is silently dropped so older LangGraph
            installs don't raise ``TypeError: invoke() got an unexpected
            keyword argument 'context'``. If your installed LangGraph version
            predates the ``context`` API, put the equivalent values under
            ``config["configurable"]`` instead.
        thread_aware: When ``True``, a single ``thread_id`` is generated the
            first time ``_agent`` is called for a given logical test case
            (identified by ``id(test_case)``) and then injected into
            ``config["configurable"]["thread_id"]`` on every subsequent call
            for that same test case. This lets a checkpointer-backed graph
            accumulate state across ``run_suite``'s ``n_runs`` loop for that
            case. Pair this with ``run_suite(..., stateful=True)`` so the
            repeated calls for one test case are guaranteed to run
            sequentially (not interleaved across threads) — see
            ``agent_regress.core.runner.run_suite`` for that contract.
        thread_id_factory: Optional zero-argument callable that returns a new
            thread id string, used when ``thread_aware=True``. Defaults to a
            simple incrementing counter (``"agent-regress-thread-<n>"``).
        operation: Optional callable ``(graph, test_case) -> Any``. When
            given, ``_agent(test_case)`` calls ``operation(graph, test_case)``
            instead of the default ``graph.invoke(state)`` path. This lets a
            caller exercise non-invoke, checkpoint-surgery methods such as
            ``graph.bulk_update_state(...)``, ``graph.abulk_update_state(...)``,
            ``graph.update_state(...)``, or ``graph.get_state(...)``, e.g.
            ``operation=lambda g, tc: g.bulk_update_state(tc["config"],
            tc["updates"])``. When ``operation`` is given,
            ``input_key``/``config``/``context``/``thread_aware`` are ignored
            for that call.

    Returns:
        An AgentCallable suitable for use with compare() or run_suite().
    """
    try:
        import langgraph  # noqa: F401, PLC0415  # type: ignore[import-untyped]
    except ImportError as exc:
        raise ImportError(
            "LangGraph integration requires langgraph. "
            "Install with: pip install agent-regress[langgraph]"
        ) from exc

    supports_context_kwarg = False
    if context is not None:
        try:
            invoke_sig = inspect.signature(graph.invoke)
            supports_context_kwarg = "context" in invoke_sig.parameters or any(
                p.kind == inspect.Parameter.VAR_KEYWORD
                for p in invoke_sig.parameters.values()
            )
        except (TypeError, ValueError):
            supports_context_kwarg = False

    thread_ids: dict[int, str] = {}
    thread_counter = itertools.count(1)

    def _next_thread_id() -> str:
        if thread_id_factory is not None:
            return thread_id_factory()
        return f"agent-regress-thread-{next(thread_counter)}"

    def _agent(test_case: dict[str, Any]) -> Any:
        if operation is not None:
            return operation(graph, test_case)

        state = _build_state(test_case, input_key)

        call_config: dict[str, Any] | None = (
            dict(config) if config is not None else None
        )

        if thread_aware:
            case_key = id(test_case)
            if case_key not in thread_ids:
                thread_ids[case_key] = _next_thread_id()
            call_config = dict(call_config) if call_config is not None else {}
            configurable = dict(call_config.get("configurable", {}))
            configurable["thread_id"] = thread_ids[case_key]
            call_config["configurable"] = configurable

        invoke_kwargs: dict[str, Any] = {}
        if call_config is not None:
            invoke_kwargs["config"] = call_config
        if context is not None and supports_context_kwarg:
            invoke_kwargs["context"] = context

        return graph.invoke(state, **invoke_kwargs)

    return _agent


def langgraph_async_runner(  # noqa: PLR0913
    graph: Any,
    input_key: str = "messages",
    store: Any = None,
    config: dict[str, Any] | None = None,
    context: dict[str, Any] | None = None,
    operation: Callable[[Any, dict[str, Any]], Awaitable[Any]] | None = None,
) -> AsyncAgentCallable:
    """Wrap a LangGraph graph as an agent-regress AsyncAgentCallable.

    The async counterpart to `langgraph_runner()`: calls
    `await graph.ainvoke(state, config=config)` instead of
    `graph.invoke(state)`, and shares the same state-building logic (see
    `_build_state`). Use this with `agent_regress.core.runner.arun_suite()`
    or `agent_regress.core.runner.concurrent_cancellation_probe()` to reach
    bugs that only manifest under a sustained async event loop (e.g.
    concurrent cancellation of in-flight calls against a shared async
    store/queue) — `langgraph_runner()`'s synchronous `.invoke()` path
    cannot exercise that code at all.

    Args:
        graph: A compiled LangGraph graph with an `.ainvoke()` method.
        input_key: Key used to pass the test case into the graph state. Same
            semantics as `langgraph_runner`'s `input_key`.
        store: Optional store instance (e.g. a LangGraph `BaseStore` /
            `AsyncPostgresStore`). LangGraph wires a compiled graph's store
            in at compile time (`graph.compile(store=...)`), not at
            `.ainvoke()` time, so there is no confirmed runtime-injection
            kwarg to forward this to. Rather than silently dropping it, this
            wrapper stashes it under `config["configurable"]["store"]` on
            every call (best-effort passthrough, via `_wire_store_into_config`)
            so it is available to any node function that reads
            `config["configurable"]`, and so a caller can inspect it. If your
            compiled graph does support a genuine store kwarg on
            `.ainvoke()`, prefer wiring the store in at compile time instead
            of relying on this parameter.
        config: Optional LangGraph ``config`` dict, passed through as
            ``graph.ainvoke(state, config=config)``. When ``store`` is also
            given, the two are merged (``store`` is stashed under
            ``config["configurable"]["store"]`` without overwriting an
            explicit ``configurable["store"]`` already present in
            ``config``).
        context: Optional LangGraph ``context`` dict for the newer
            ``context`` API, forwarded as ``graph.ainvoke(state,
            context=context)`` only when given (``None``, the default,
            forwards nothing extra, so older LangGraph installs whose
            `.ainvoke()` predates the `context` API are unaffected).
        operation: Optional async callable ``(graph, test_case) -> Awaitable[Any]``.
            When given, ``_agent(test_case)`` calls
            ``await operation(graph, test_case)`` instead of the default
            ``await graph.ainvoke(state, ...)`` path. This lets a caller
            exercise non-invoke, checkpoint-surgery methods such as
            ``graph.abulk_update_state(...)``, ``graph.aupdate_state(...)``,
            or ``graph.aget_state(...)``, e.g. ``operation=lambda g, tc:
            g.abulk_update_state(tc["config"], tc["updates"])``. When
            ``operation`` is given, ``input_key``/``store``/``config``/
            ``context`` are ignored for that call.

    Returns:
        An AsyncAgentCallable suitable for use with `arun_suite()` or
        `concurrent_cancellation_probe()`.
    """
    try:
        import langgraph  # noqa: F401, PLC0415  # type: ignore[import-untyped]
    except ImportError as exc:
        raise ImportError(
            "LangGraph integration requires langgraph. "
            "Install with: pip install agent-regress[langgraph]"
        ) from exc

    merged_config = _wire_store_into_config(config, store)

    async def _agent(test_case: dict[str, Any]) -> Any:
        if operation is not None:
            return await operation(graph, test_case)

        state = _build_state(test_case, input_key)
        invoke_kwargs: dict[str, Any] = {"config": merged_config}
        if context is not None:
            invoke_kwargs["context"] = context
        return await graph.ainvoke(state, **invoke_kwargs)

    return _agent


def langgraph_interrupt_resume_runner(
    graph: Any,
    input_key: str = "messages",
    resume_value: Any = None,
    config: dict[str, Any] | None = None,
) -> AgentCallable:
    """Wrap a LangGraph graph to exercise the interrupt-then-resume cycle.

    Purpose-built for the risk class behind PR #3126 ("allow ToolNode to
    accept ToolCalls"): a node re-executing (double-running) a tool call
    after a graph resumes from an `interrupt()`. `langgraph_runner()`'s
    `operation=`/`thread_aware=` params already let a caller hand-roll this
    sequence manually; this function is the built-in convenience for the
    common case so callers don't have to re-derive the interrupt-detection
    logic themselves.

    Sequence per test case:
        1. ``graph.invoke(state, config=call_config)`` — same state-building
           as `langgraph_runner` (see `_build_state`). A `thread_id` is
           auto-generated per test case (stable across the two invokes for
           that case, distinct across test cases) and injected into
           ``call_config["configurable"]["thread_id"]`` unless the caller's
           ``config`` already supplies one — a checkpointer-backed graph
           needs a stable thread id to resume the *same* paused checkpoint.
        2. ``graph.get_state(call_config)`` is inspected to determine whether
           the graph actually interrupted. This was verified against the
           installed `langgraph` 1.2.6 source
           (`langgraph/types.py::StateSnapshot`): a `StateSnapshot` exposes
           `.next` (tuple of node names scheduled to run next — non-empty
           when paused at an interrupt) and `.interrupts` (tuple of pending
           `Interrupt` objects), and each entry in `.tasks`
           (tuple of `PregelTask`) has its own `.interrupts` tuple. This
           function treats the graph as interrupted if any of those three
           signals is non-empty, which is robust to a LangGraph version that
           only surfaces the pause on one of them.
        3. If interrupted, resume via ``graph.invoke(Command(resume=
           resume_value), config=call_config)`` (``Command`` imported from
           ``langgraph.types``, confirmed present with a ``resume=`` keyword
           on the installed version). The resumed call's return value
           replaces the initial call's return value as the "final" result.
        4. Return a dict bundling enough information for
           `agent_regress.core.scorer.tool_call_trace_scorer` (and other
           scorers) to detect double-execution across the interrupt/resume
           boundary:
           ``{"result": <final invoke() return value>, "interrupted": bool,
           "messages": <final result["messages"] if the result is a dict
           with that key, else None>}``. Because `tool_call_trace_scorer`
           reads `output["messages"]` directly, pass this dict straight to
           it as `output` — if a tool node re-executed after resume, a
           `tool_call_id` will appear more than once in `messages` and
           `tool_call_trace_scorer` will score below 1.0 for that id.

    Args:
        graph: A compiled LangGraph graph with `.invoke()` and `.get_state()`
            methods, compiled with a checkpointer (required by LangGraph for
            `graph.get_state()` to return anything other than raising
            `ValueError: No checkpointer set`).
        input_key: Key used to pass the test case into the graph state. Same
            semantics as `langgraph_runner`'s `input_key`.
        resume_value: Value forwarded as `Command(resume=resume_value)` when
            resuming an interrupted graph. Defaults to `None`, matching
            `Command`'s own default.
        config: Optional base LangGraph `config` dict, merged with the
            auto-generated `thread_id` the same way `langgraph_runner`'s
            `thread_aware=True` merges it (an explicit
            `config["configurable"]["thread_id"]` is preserved and not
            overwritten). Defaults to `None`.

    Returns:
        An AgentCallable suitable for use with `compare()` or `run_suite()`.

    Limitations (documented, not silently assumed):
        - This function does not itself decide *when* a graph should
          interrupt — that is entirely up to how the wrapped graph's nodes
          call `interrupt()`. If a test case's input never triggers an
          `interrupt()`, step 3 above is simply skipped and
          `interrupted=False` is returned; this is a real (not fake)
          no-interrupt result, not an error.
        - Only a single interrupt/resume cycle is exercised. A graph that
          interrupts more than once per run (nested/sequential interrupts)
          will only have its first pause resumed here; the returned
          `"result"` reflects whatever LangGraph does when `Command(resume=
          resume_value)` is invoked against a still-further-interrupted
          graph (typically it just pauses again, unresolved by this
          function).
    """
    try:
        import langgraph  # noqa: F401, PLC0415  # type: ignore[import-untyped]
        from langgraph.types import Command  # noqa: PLC0415
    except ImportError as exc:
        raise ImportError(
            "LangGraph integration requires langgraph. "
            "Install with: pip install agent-regress[langgraph]"
        ) from exc

    thread_counter = itertools.count(1)

    def _next_thread_id() -> str:
        return f"agent-regress-interrupt-thread-{next(thread_counter)}"

    def _is_interrupted(snapshot: Any) -> bool:
        if bool(getattr(snapshot, "next", ())):
            return True
        if bool(getattr(snapshot, "interrupts", ())):
            return True
        tasks = getattr(snapshot, "tasks", ())
        return any(bool(getattr(task, "interrupts", ())) for task in tasks)

    def _agent(test_case: dict[str, Any]) -> dict[str, Any]:
        state = _build_state(test_case, input_key)

        call_config: dict[str, Any] = dict(config) if config is not None else {}
        configurable = dict(call_config.get("configurable", {}))
        configurable.setdefault("thread_id", _next_thread_id())
        call_config["configurable"] = configurable

        result = graph.invoke(state, config=call_config)

        snapshot = graph.get_state(call_config)
        interrupted = _is_interrupted(snapshot)

        if interrupted:
            result = graph.invoke(Command(resume=resume_value), config=call_config)

        messages = result.get("messages") if isinstance(result, dict) else None

        return {"result": result, "interrupted": interrupted, "messages": messages}

    return _agent


_CACHE_ATTR_NAMES = ("cache", "_cache", "cache_policy")


def graph_has_cache(graph: Any) -> bool:
    """Best-effort check for whether a compiled graph has node/task-level caching.

    LangGraph's `cache_policy` (added in PR #4486) lets individual nodes/tasks
    cache their results, keyed on `hash(node_name, args)` with no step/thread
    component. When present, repeated calls against the same compiled graph
    object within a `run_suite()` `n_runs` loop can be served from cache
    instead of re-executed, silently collapsing that node's contribution to
    measured variance.

    This function does NOT call any LangGraph API and does not require
    LangGraph to be installed. It performs a `hasattr`-based heuristic: it
    checks the graph object itself, and (for a compiled
    `Pregel`/`CompiledStateGraph` graph that exposes its nodes via a `nodes`
    mapping/iterable, matching how LangGraph surfaces per-node config today)
    each of its nodes, for a non-null cache-like attribute. Checked attribute
    names: `cache`, `_cache`, `cache_policy`.

    Limitations (documented, not silently assumed):
        - This is a heuristic, not an authoritative answer. LangGraph does
          not expose a single public "does this graph use caching" API, so a
          compiled graph could have per-node `cache_policy` set without any
          of the checked attributes being non-null in a future LangGraph
          version (false negative), or a graph could expose one of these
          attribute names for an unrelated purpose (false positive).
        - It never raises: any object without the checked attributes (e.g. a
          plain mock, or a real compiled graph before LangGraph changes its
          internals) simply returns `False`.
        - Callers should treat `True` as "likely has caching, investigate
          before assuming repeated-sampling variance is real" and `False` as
          "no evidence of caching found," not as a hard guarantee either way.

    Args:
        graph: A compiled LangGraph graph object (or any object; this
            function is safe to call on non-graph objects too).

    Returns:
        `True` if a non-null cache-like attribute was found, `False`
        otherwise.
    """

    def _has_nonnull_cache_attr(obj: Any) -> bool:
        return any(getattr(obj, name, None) is not None for name in _CACHE_ATTR_NAMES)

    if _has_nonnull_cache_attr(graph):
        return True

    nodes = getattr(graph, "nodes", None)
    if nodes is None:
        return False

    try:
        node_values = nodes.values() if hasattr(nodes, "values") else nodes
        return any(_has_nonnull_cache_attr(node) for node in node_values)
    except TypeError:
        return False
