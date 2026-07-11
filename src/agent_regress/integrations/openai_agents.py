"""OpenAI Agents SDK runner integration."""

from __future__ import annotations

import asyncio
import concurrent.futures
import contextlib
import dataclasses
import inspect
from collections.abc import Callable, Coroutine
from typing import Any

from agent_regress.core.runner import AgentCallable


@dataclasses.dataclass(frozen=True)
class TracedResult:
    """Return value of ``openai_agents_runner(..., capture_trace=True)``.

    Attributes:
        output: The normal agent output — identical to what the runner would
            return when ``capture_trace=False``.
        trace: Best-effort captured telemetry for the run. Contains:

            - ``"run_config"``: the resolved ``agents.RunConfig`` used for the
              top-level run, expanded to a field-name -> value dict.
            - ``"tool_calls"``: a list of exported ``FunctionSpanData`` dicts for
              every tool-call span observed via the Agents SDK tracing processor
              hook during the run.
            - ``"nested_run_configs"``: one entry per *nested* ``agents.Runner.run``
              call observed during the top-level run (e.g. an agent invoked via
              ``Agent.as_tool()``), each shaped
              ``{"call_index": int, "agent_name": str | None,
              "run_config_id": int | None, "same_object_as_top_level_run_config":
              bool}``. The SDK does not attach any ``RunConfig``-shaped data to
              span/trace data itself (verified against the installed
              ``agents`` SDK: none of ``AgentSpanData``/``FunctionSpanData``/etc.
              carry a ``run_config`` field), so this is captured by temporarily
              wrapping ``agents.Runner.run`` for the duration of the call and
              recording, per nested invocation, whether the ``RunConfig`` object
              it received is the *same object* (``is``) as the top-level run's
              ``RunConfig`` — which is exactly the signal that distinguishes
              "nested call inherited the parent's RunConfig" (the SDK threads the
              same object through ``ToolContext.run_config`` when
              ``Agent.as_tool(run_config=...)`` is not given an explicit
              override; see ``agents/agent.py``'s ``_run_agent_impl`` and
              ``agents/run_internal/tool_execution.py``) from "nested call got a
              different/fresh RunConfig". This cannot disambiguate *which* tool
              call in ``tool_calls`` triggered a given nested run beyond the
              captured ``agent_name`` — that finer attribution is not exposed by
              the SDK's tracing spans either.
            - ``"converted_tool_outputs"``: one entry per
              ``agents.models.chatcmpl_converter.Converter.items_to_messages``
              call observed during the run (the shared conversion choke point
              used by the Chat Completions, LiteLLM, and any-llm model
              backends), each shaped ``{"pre_conversion_outputs":
              [{"call_id": ..., "output": ...}, ...],
              "post_conversion_tool_messages": [{"role": "tool",
              "tool_call_id": ..., "content": ...}, ...]}``. This exists because
              ``FunctionSpanData.export()`` (what feeds ``tool_calls`` above)
              stringifies tool output at span-capture time, *before* any
              converter runs, so ``tool_calls`` alone cannot show whether
              non-text tool content (images, files, ...) survived the
              Chat-Completions-style conversion. Captured by temporarily
              wrapping ``Converter.items_to_messages`` for the duration of the
              call; empty when the installed SDK does not expose
              ``agents.models.chatcmpl_converter.Converter`` (e.g. an older/newer
              SDK layout) or when the run's model never goes through it (e.g. a
              pure Responses-API model with no Chat-Completions-shaped calls).

            Both ``nested_run_configs`` and ``converted_tool_outputs`` are
            captured by globally monkeypatching ``agents.Runner.run`` /
            ``Converter.items_to_messages`` for the duration of one
            ``capture_trace=True`` call (restored in a ``finally``, same
            defensive pattern as the trace-processor restore below) — like the
            existing ``tool_calls`` capture, this is not safe to rely on across
            *concurrently overlapping* ``capture_trace=True`` calls (e.g. via
            ``arun_suite``/threaded ``compare()``), since the patch is process-wide
            mutable state, not call-scoped.
    """

    output: Any
    trace: dict[str, Any]


def _run_coroutine_sync(coro_fn: Callable[[], Coroutine[Any, Any, Any]]) -> Any:
    """Run ``coro_fn()`` to completion, from sync or already-async contexts alike.

    Handles both synchronous and async (Jupyter / already-running-loop) contexts
    by spawning a background thread when a running event loop is detected.
    """
    try:
        asyncio.get_running_loop()
        loop_running = True
    except RuntimeError:
        loop_running = False

    if loop_running:
        # A loop is already running (e.g. Jupyter) — run in a fresh thread.
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:
            return ex.submit(asyncio.run, coro_fn()).result()
    return asyncio.run(coro_fn())


def _extract_function_call_output_items(items: Any) -> list[dict[str, Any]]:
    """Pull ``{"call_id", "output"}`` for every ``function_call_output`` item.

    ``items`` mirrors the ``items`` argument of
    ``agents.models.chatcmpl_converter.Converter.items_to_messages`` — either a
    plain string (no function-call-output items possible) or an iterable of
    response input item dicts. ``output`` is captured raw (pre-conversion),
    whatever shape the SDK gave it (string, or a list of content-part dicts for
    non-text/multimodal tool output).
    """
    if isinstance(items, str):
        return []
    extracted: list[dict[str, Any]] = []
    with contextlib.suppress(TypeError):
        for item in items:
            if isinstance(item, dict) and item.get("type") == "function_call_output":
                extracted.append(
                    {"call_id": item.get("call_id"), "output": item.get("output")}
                )
    return extracted


def openai_agents_runner(  # noqa: PLR0915
    agent: Any,
    *,
    capture_trace: bool = False,
    session: Any | None = None,
    session_factory: Callable[[], Any] | None = None,
    session_aware: bool = False,
) -> AgentCallable:
    """Wrap an OpenAI Agents SDK agent as an agent-regress AgentCallable.

    Handles both synchronous and async (Jupyter / already-running-loop) contexts
    by spawning a background thread when a running event loop is detected.

    Args:
        agent: An OpenAI Agents SDK ``Agent`` instance. Run via the real SDK
            entrypoint, the module-level ``agents.Runner.run(agent, query, ...)``
            (``agents.Agent`` itself has no ``.run()`` method).
        capture_trace: When True, attach an Agents SDK tracing processor before
            the run and return ``TracedResult(output=<normal output>, trace={...})``
            instead of the raw output. Default False preserves the original return
            value (the run's ``final_output``) unchanged — this is the
            backward-compatibility contract. See ``TracedResult`` for the full
            shape of ``trace``, including the ``nested_run_configs`` and
            ``converted_tool_outputs`` fields.
        session: An optional ``agents.Session`` implementer (e.g. a
            ``MongoDBSession``-shaped object) to pass through to
            ``agents.Runner.run(agent, query, session=session)`` for multi-turn /
            persistent-memory continuity. Takes precedence over ``session_factory``
            when both are given. Default None preserves current behavior exactly.
        session_factory: An optional zero-arg callable invoked once per call to
            build a fresh session object, used the same way as ``session``. Ignored
            when ``session`` is given. By default (``session_aware=False``) it is
            invoked fresh on *every* call, so there is no continuity across
            repeated calls for the same test case.
        session_aware: When True, ``session_factory`` (not ``session``, which is
            already a single built object and unaffected by this flag) is invoked
            at most once per logical test case — the first time ``_agent`` is
            called for a given test case (keyed by ``id(test_case)``, mirroring
            ``langgraph_runner``'s ``thread_aware=`` pattern exactly) — and that
            same session object is reused on every subsequent call for that same
            test case, giving a real session-backed multi-turn continuity
            primitive. A different test case always gets its own fresh session.
            Default False preserves the current per-call-fresh behavior exactly.
            Pair this with ``run_suite(..., stateful=True)`` so the repeated
            calls for one test case's ``n_runs`` loop are guaranteed to run
            sequentially (not interleaved across threads) — see
            ``agent_regress.core.runner.run_suite`` and
            ``langgraph_runner``'s ``thread_aware`` docstring for the same
            contract.

    Returns:
        An AgentCallable suitable for use with compare() or run_suite().
    """
    try:
        import agents  # noqa: PLC0415  # type: ignore[import-untyped]
    except ImportError as exc:
        raise ImportError(
            "OpenAI Agents SDK integration requires openai-agents. "
            "Install with: pip install agent-regress[openai-agents]"
        ) from exc

    session_by_case: dict[int, Any] = {}

    def _resolve_session(test_case: dict[str, Any] | None) -> Any:
        if session is not None:
            return session
        if session_factory is not None:
            if session_aware and test_case is not None:
                case_key = id(test_case)
                if case_key not in session_by_case:
                    session_by_case[case_key] = session_factory()
                return session_by_case[case_key]
            return session_factory()
        return None

    async def _run_traced(query: str, test_case: dict[str, Any] | None) -> TracedResult:
        tool_calls: list[dict[str, Any]] = []
        nested_run_configs: list[dict[str, Any]] = []
        converted_tool_outputs: list[dict[str, Any]] = []

        class _ToolCallCollector(agents.tracing.TracingProcessor):  # type: ignore[misc]
            def on_trace_start(self, trace: Any) -> None:
                return None

            def on_trace_end(self, trace: Any) -> None:
                return None

            def on_span_start(self, span: Any) -> None:
                return None

            def on_span_end(self, span: Any) -> None:
                span_data = getattr(span, "span_data", None)
                if span_data is None:
                    return
                if getattr(span_data, "type", None) == "function":
                    with contextlib.suppress(Exception):
                        tool_calls.append(span_data.export())

            def shutdown(self) -> None:
                return None

            def force_flush(self) -> None:
                return None

        collector = _ToolCallCollector()
        provider = agents.tracing.get_trace_provider()
        # `_multi_processor`/`_processors` are private SDK internals with no
        # public accessor for restoring the pre-capture processor list; both
        # lookups are getattr-guarded and the restore below is
        # best-effort (contextlib.suppress) so an SDK internals change
        # degrades to "processors not restored" rather than crashing.
        multi_processor = getattr(provider, "_multi_processor", None)
        original_processors: tuple[Any, ...] | None = None
        if multi_processor is not None:
            original_processors = getattr(multi_processor, "_processors", None)

        run_config = agents.RunConfig()

        # `agents.Runner.run` is also the entrypoint used internally for nested
        # `Agent.as_tool()` calls (see agents/agent.py's `_run_agent_impl`), so
        # wrapping it for the duration of the top-level call is the only way to
        # observe the RunConfig each nested call actually received — none of the
        # SDK's span/trace data types carry a RunConfig. The top-level call below
        # goes through `original_runner_run` directly (bypassing the patch), so
        # `nested_run_configs` only ever contains genuinely nested invocations.
        original_runner_run = agents.Runner.run

        async def _patched_runner_run(*args: Any, **kwargs: Any) -> Any:
            call_run_config = kwargs.get("run_config")
            nested_starting_agent = kwargs.get(
                "starting_agent", args[0] if args else None
            )
            nested_run_configs.append(
                {
                    "call_index": len(nested_run_configs),
                    "agent_name": getattr(nested_starting_agent, "name", None),
                    "run_config_id": (
                        id(call_run_config) if call_run_config is not None else None
                    ),
                    "same_object_as_top_level_run_config": call_run_config
                    is run_config,
                }
            )
            return await original_runner_run(*args, **kwargs)

        # `Converter.items_to_messages` is the shared conversion choke point used
        # by the Chat Completions, LiteLLM, and any-llm model backends alike
        # (verified against the installed SDK: all three call sites route
        # through `agents.models.chatcmpl_converter.Converter.items_to_messages`).
        # It runs downstream of `FunctionSpanData.export()` (which stringifies
        # tool output at span-capture time), so wrapping it is the only way to
        # see whether non-text tool output survived the conversion. Guarded:
        # older/newer SDK layouts that don't expose this module simply get an
        # empty `converted_tool_outputs` list rather than an error.
        converter_cls: Any = None
        original_items_to_messages: Any = None
        try:
            from agents.models.chatcmpl_converter import (  # noqa: PLC0415
                Converter as _Converter,
            )

            converter_cls = _Converter
            original_items_to_messages = _Converter.items_to_messages
        except ImportError:
            converter_cls = None

        def _patched_items_to_messages(items: Any, *args: Any, **kwargs: Any) -> Any:
            pre_conversion_outputs = _extract_function_call_output_items(items)
            messages = original_items_to_messages(items, *args, **kwargs)
            if pre_conversion_outputs:
                post_conversion_tool_messages = [
                    message
                    for message in messages
                    if isinstance(message, dict) and message.get("role") == "tool"
                ]
                converted_tool_outputs.append(
                    {
                        "pre_conversion_outputs": pre_conversion_outputs,
                        "post_conversion_tool_messages": post_conversion_tool_messages,
                    }
                )
            return messages

        agents.add_trace_processor(collector)
        agents.Runner.run = _patched_runner_run
        if converter_cls is not None:
            converter_cls.items_to_messages = _patched_items_to_messages
        try:
            result = await original_runner_run(
                agent, query, session=_resolve_session(test_case), run_config=run_config
            )
        finally:
            agents.Runner.run = original_runner_run
            if converter_cls is not None:
                converter_cls.items_to_messages = original_items_to_messages
            if multi_processor is not None and original_processors is not None:
                with contextlib.suppress(Exception):
                    multi_processor.set_processors(list(original_processors))

        trace: dict[str, Any] = {
            "run_config": {
                field.name: getattr(run_config, field.name)
                for field in dataclasses.fields(run_config)
            },
            "tool_calls": tool_calls,
            "nested_run_configs": nested_run_configs,
            "converted_tool_outputs": converted_tool_outputs,
        }
        return TracedResult(output=result.final_output, trace=trace)

    async def _run(query: str, test_case: dict[str, Any] | None) -> Any:
        if capture_trace:
            return await _run_traced(query, test_case)
        result = await agents.Runner.run(
            agent, query, session=_resolve_session(test_case)
        )
        return result.final_output

    def _agent(test_case: dict[str, Any]) -> Any:
        query = test_case.get("query", str(test_case))
        return _run_coroutine_sync(lambda: _run(query, test_case))

    return _agent


async def _enter_realtime_session(session: Any) -> bool:
    """Enter ``session``'s async context manager if it has one.

    Returns whether it was entered.
    """
    aenter = getattr(session, "__aenter__", None)
    if aenter is None:
        return False
    await aenter()
    return True


async def _exit_realtime_session(session: Any, entered: bool) -> None:
    """Tear down ``session`` via its async context manager, else a best-effort close().

    Falls back to a sync-or-async ``close()`` method when the session was never
    entered as an async context manager.
    """
    if entered:
        aexit = getattr(session, "__aexit__", None)
        if aexit is not None:
            await aexit(None, None, None)
        return
    close = getattr(session, "close", None)
    if close is None:
        return
    maybe_awaitable = close()
    if inspect.isawaitable(maybe_awaitable):
        await maybe_awaitable


async def _send_scripted_inputs(session: Any, scripted_inputs: list[Any]) -> None:
    """Feed each scripted input into ``session`` via ``send_message``/``send``.

    Raises TypeError if the session exposes neither method.
    """
    send = getattr(session, "send_message", None) or getattr(session, "send", None)
    if send is None:
        raise TypeError(
            "realtime session object must expose a send_message(...) or "
            "send(...) coroutine method"
        )
    for scripted_input in scripted_inputs:
        await send(scripted_input)


async def _collect_realtime_tool_events(
    session: Any, max_events: int | None
) -> list[Any]:
    """Consume ``session``'s async event stream, keeping only tool start/end events."""
    collected: list[Any] = []
    if not hasattr(session, "__aiter__"):
        return collected
    count = 0
    async for event in session:
        type_name = type(event).__name__
        if "RealtimeToolStart" in type_name or "RealtimeToolEnd" in type_name:
            collected.append(event)
        count += 1
        if max_events is not None and count >= max_events:
            break
    return collected


def openai_agents_realtime_runner(
    session_factory: Callable[[], Any],
    scripted_inputs: list[Any],
    *,
    max_events: int | None = None,
) -> AgentCallable:
    """Wrap an OpenAI Agents SDK realtime session as an agent-regress AgentCallable.

    Drives a realtime session over a fixed list of scripted inputs and collects
    any ``RealtimeToolStart``/``RealtimeToolEnd``-shaped events it observes into a
    scoreable dict: ``{"events": [...]}``.

    The session object returned by ``session_factory()`` is duck-typed like
    ``agents.realtime.RealtimeSession`` and, on a best-effort basis, is expected to
    support:

    - The async context manager protocol (``__aenter__``/``__aexit__``), used to
      enter/exit the session when present.
    - A ``send_message(...)`` (or ``send(...)``) coroutine method, used to feed
      each entry of ``scripted_inputs`` into the session, in order.
    - Async iteration (``__aiter__``/``__anext__``) yielding realtime events. Every
      event whose class name contains ``"RealtimeToolStart"`` or
      ``"RealtimeToolEnd"`` is collected, in order observed.
    - An optional ``close()`` method (sync or async), used as a fallback teardown
      when the session does not support the async context manager protocol.

    Args:
        session_factory: Zero-arg callable that returns a fresh realtime-session-like
            object for each call.
        scripted_inputs: Ordered inputs sent into the session via
            ``send_message``/``send`` before consuming its event stream.
        max_events: Optional cap on the number of events consumed from the
            session's event stream before stopping — useful for bounding an
            otherwise-unbounded live session. Default None consumes events until
            the stream itself ends (e.g. a finite test double / scripted replay).

    Returns:
        An AgentCallable suitable for use with compare() or run_suite(); each call
        returns ``{"events": [<collected RealtimeToolStart/RealtimeToolEnd events>]}``.
    """

    async def _drive() -> dict[str, Any]:
        session = session_factory()
        entered = await _enter_realtime_session(session)
        try:
            await _send_scripted_inputs(session, scripted_inputs)
            events = await _collect_realtime_tool_events(session, max_events)
            return {"events": events}
        finally:
            await _exit_realtime_session(session, entered)

    def _agent(test_case: dict[str, Any]) -> Any:
        del test_case  # unused: scripted_inputs drive the session, not the test case
        return _run_coroutine_sync(_drive)

    return _agent
