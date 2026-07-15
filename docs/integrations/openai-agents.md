# OpenAI Agents SDK Integration

## Install

```bash
pip install agent-regress-cli[openai-agents]
```

## Usage

```python
from agent_regress import compare
from agent_regress.integrations.openai_agents import openai_agents_runner

# Your OpenAI Agents SDK agent instances
agent_v1 = build_agent(instructions="v1 instructions")
agent_v2 = build_agent(instructions="v2 instructions")

def scorer(output: str, test_case: dict) -> float:
    return 1.0 if test_case["expected"] in output else 0.0

report = compare(
    version_a=openai_agents_runner(agent_v1),
    version_b=openai_agents_runner(agent_v2),
    test_suite=test_suite,
    n_runs=50,
    scorer=scorer,
)
print(report)
```

Internally, `openai_agents_runner()` drives the real SDK entrypoint —
`agents.Runner.run(agent, query, ...)` — since `agents.Agent` itself has no
`.run()` method.

## Trace capture (opt-in)

Pass `capture_trace=True` to get back a `TracedResult(output=..., trace={...})`
instead of the raw output. Default is `False`, which preserves the original
return value unchanged. `trace` includes:

- `"run_config"`: the resolved `RunConfig` used for the top-level run, as a dict.
- `"tool_calls"`: the list of tool-call spans observed via an Agents SDK tracing
  processor during the run.
- `"nested_run_configs"`: one entry per *nested* `agents.Runner.run` call observed
  during the run (e.g. an agent invoked via `Agent.as_tool()`), each recording
  the nested agent's name and whether it received the exact same `RunConfig`
  object as the top-level run (`"same_object_as_top_level_run_config"`) — the
  signal that distinguishes "the nested call inherited the parent's RunConfig"
  from "it got a different/fresh one". The SDK's span/trace data types carry no
  `RunConfig`-shaped fields, so this is captured by temporarily wrapping
  `agents.Runner.run` for the duration of the call (restored afterward); it
  can't attribute a nested call to a specific tool-call span beyond the nested
  agent's name.
- `"converted_tool_outputs"`: one entry per
  `agents.models.chatcmpl_converter.Converter.items_to_messages` call observed
  during the run (the conversion choke point shared by the Chat Completions,
  LiteLLM, and any-llm model backends), each recording the raw
  pre-conversion tool output alongside the post-conversion `"tool"`-role
  message(s). This exists because the tool-call spans that feed `"tool_calls"`
  stringify their output at capture time, before any conversion runs, so they
  alone can't show whether non-text tool content (images, files, ...) survived
  conversion — `"converted_tool_outputs"` can. Empty when the installed SDK
  doesn't expose `Converter` or the run's model never routes through it (e.g. a
  pure Responses-API model).

```python
from agent_regress.integrations.openai_agents import openai_agents_runner, TracedResult

traced_runner = openai_agents_runner(agent_v1, capture_trace=True)
traced = traced_runner({"query": "what is 2+2?"})
assert isinstance(traced, TracedResult)
print(traced.trace["tool_calls"])
print(traced.trace["nested_run_configs"])
print(traced.trace["converted_tool_outputs"])
```

`nested_run_configs` and `converted_tool_outputs` are both captured by
temporarily monkeypatching process-wide SDK state for the duration of one
`capture_trace=True` call (restored in a `finally`) — like `tool_calls`, don't
rely on them across *concurrently overlapping* `capture_trace=True` calls (e.g.
via `arun_suite`/threaded `compare()`).

Pair `capture_trace=True` with `agent_regress.core.scorer.structured_content_scorer`
to score against these fields directly — it accepts `test_case["expected_trace"]`
and `test_case["expected_converted_tool_output_types"]` (a `call_id -> expected
content types` dict, e.g. `{"call_1": ["text", "image_url"]}`) for asserting a
tool's non-text output actually survived conversion.

## Session / multi-turn continuity (opt-in)

Pass `session=` (an `agents.Session` implementer, e.g. `MongoDBSession`) or
`session_factory=` (a zero-arg callable that builds one) to have it passed
through to `agents.Runner.run(agent, query, session=...)`:

```python
runner = openai_agents_runner(agent_v1, session=my_mongodb_session)
```

By default, `session_factory=` is invoked fresh on *every* call, so there's no
continuity between calls. Pass `session_aware=True` to build one session per
logical test case instead — the first time a given test case (keyed by
`id(test_case)`, mirroring `langgraph_runner`'s `thread_aware=`) is run, and
reused on every subsequent call for that same test case:

```python
from agent_regress.core.runner import run_suite

runner = openai_agents_runner(
    agent_v1,
    session_factory=lambda: MongoDBSession(...),
    session_aware=True,
)
# stateful=True guarantees each test case's n_runs loop stays sequential, so
# the reused session accumulates state in the right order.
scores = run_suite(runner, test_suite, n_runs=5, scorer=scorer, stateful=True)
```

`session_aware=` only affects `session_factory=`; an already-built `session=`
object is unaffected. Default `False` preserves the original per-call-fresh
behavior exactly.

## Realtime sessions

`openai_agents_realtime_runner(session_factory, scripted_inputs)` drives a
realtime session (duck-typed like `agents.realtime.RealtimeSession`) over a fixed
list of scripted inputs and collects any `RealtimeToolStart`/`RealtimeToolEnd`
events into a scoreable `{"events": [...]}` dict:

```python
from agent_regress.integrations.openai_agents import openai_agents_realtime_runner

runner = openai_agents_realtime_runner(
    session_factory=lambda: my_realtime_runner.run(),
    scripted_inputs=["hi", "book me a flight"],
)
report = compare(version_a=runner, version_b=runner_v2, test_suite=[{}], scorer=my_scorer)
```
