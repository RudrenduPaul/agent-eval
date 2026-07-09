# OpenAI Agents SDK Integration

## Install

```bash
pip install agent-regress[openai-agents]
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
instead of the raw output. `trace` includes the resolved `RunConfig` used for the
run and the list of tool-call spans observed via an Agents SDK tracing processor.
Default is `False`, which preserves the original return value unchanged.

```python
from agent_regress.integrations.openai_agents import openai_agents_runner, TracedResult

traced_runner = openai_agents_runner(agent_v1, capture_trace=True)
traced = traced_runner({"query": "what is 2+2?"})
assert isinstance(traced, TracedResult)
print(traced.trace["tool_calls"])
```

## Session / multi-turn continuity (opt-in)

Pass `session=` (an `agents.Session` implementer, e.g. `MongoDBSession`) or
`session_factory=` (a zero-arg callable that builds one) to have it passed
through to `agents.Runner.run(agent, query, session=...)`:

```python
runner = openai_agents_runner(agent_v1, session=my_mongodb_session)
```

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
