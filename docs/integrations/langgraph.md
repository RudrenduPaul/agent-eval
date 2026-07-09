# LangGraph Integration

## Install

```bash
pip install agent-regress[langgraph]
```

## Usage

```python
from agent_regress import compare
from agent_regress.integrations.langgraph import langgraph_runner

# Build your graphs
graph_v1 = build_graph(model="gpt-4o", prompt_version="v1")
graph_v2 = build_graph(model="gpt-4o", prompt_version="v2")

def scorer(output: dict, test_case: dict) -> float:
    return 1.0 if output.get("answer") == test_case["expected"] else 0.0

report = compare(
    version_a=langgraph_runner(graph_v1),
    version_b=langgraph_runner(graph_v2),
    test_suite=test_suite,
    n_runs=50,
    scorer=scorer,
)
print(report)
report.assert_stable()
```

## Config / context passthrough

Pass a `config` and/or `context` dict that is forwarded on every call:

```python
agent = langgraph_runner(
    graph,
    config={"configurable": {"model": "gpt-4o"}},
    context={"user_id": "u1"},  # only forwarded if graph.invoke() accepts context=
)
```

`context` support depends on your installed LangGraph version. LangGraph
added a `context` API alongside `config` in newer releases; `langgraph_runner`
inspects `graph.invoke`'s signature at wrap time and only forwards `context=`
if it's actually accepted, so older installs never see a `TypeError`. On
older versions, put the equivalent values under `config["configurable"]`
instead.

## Thread-aware / checkpoint continuity

Set `thread_aware=True` to give each logical test case its own stable
`thread_id`, injected into `config["configurable"]["thread_id"]` on every
call for that case. Combined with `run_suite(..., stateful=True)`, this lets
a checkpointer-backed graph accumulate state across the `n_runs` loop for a
single test case, because `run_suite` guarantees (by construction) that one
test case's repeated calls always run sequentially on a single thread:

```python
from agent_regress.core.runner import run_suite

agent = langgraph_runner(graph, thread_aware=True)
scores = run_suite(agent, test_suite, n_runs=50, scorer=scorer, stateful=True)
```

Pass `thread_id_factory` to control how thread ids are generated (defaults
to a simple incrementing counter):

```python
import uuid

agent = langgraph_runner(
    graph, thread_aware=True, thread_id_factory=lambda: str(uuid.uuid4())
)
```

## Exercising non-invoke / checkpoint-surgery methods

`langgraph_runner`'s default path only ever calls `graph.invoke(...)`. To
exercise other Pregel-protocol methods -- `update_state`, `get_state`,
`bulk_update_state`/`abulk_update_state` -- pass `operation`, a
`(graph, test_case) -> Any` callable that replaces the default `.invoke()`
call entirely:

```python
agent = langgraph_runner(
    graph,
    operation=lambda g, tc: g.bulk_update_state(tc["config"], tc["updates"]),
)
```

## Detecting node/task-level caching (avoid collapsed repeated-sampling variance)

LangGraph supports a per-node/task `cache_policy` that caches results keyed
on `hash(node_name, args)`, with no step/thread component. If your compiled
graph uses this, calling the same test case repeatedly inside
`run_suite`'s `n_runs` loop can silently be served from cache instead of
re-executed -- collapsing that node's contribution to measured variance and
making your comparison look more stable than it actually is.

Use `graph_has_cache(graph)` to check before deciding whether you need to
defeat that cache:

```python
from agent_regress.integrations.langgraph import graph_has_cache, langgraph_runner

if graph_has_cache(graph):
    print("This graph appears to have node/task caching enabled.")
```

`graph_has_cache` is a best-effort, `hasattr`-based heuristic (it checks for
non-null `cache` / `_cache` / `cache_policy` attributes on the graph and its
nodes) -- it does not call any LangGraph API and does not require LangGraph
to be installed. Treat `True` as "likely cached, investigate" and `False` as
"no evidence found," not as an authoritative answer either way. See its
docstring for full limitations.

`langgraph_runner` never calls `graph_has_cache` automatically, so this
check never changes runtime behavior on its own -- it's purely informational
for callers deciding whether to pass `cache_bust_key_fn` to `run_suite`.

If caching is present (or even suspected), pass `cache_bust_key_fn` to
`run_suite` to inject a per-run nonce field into the test case before each
call, which your graph/agent wrapper can thread through to defeat the
SUT-side cache:

```python
import uuid

from agent_regress.core.runner import run_suite

def bust_cache(test_case: dict, run_index: int) -> dict:
    return {"_cache_bust": str(uuid.uuid4())}

scores = run_suite(
    agent,
    test_suite,
    n_runs=50,
    scorer=scorer,
    cache_bust_key_fn=bust_cache,
)
```

`run_suite` also emits a `UserWarning` if every single score across every
test case and every run comes back byte-identical with `n_runs >= 10` --
that pattern is statistically implausible for anything but a fully
cached/deterministic-and-cached system under test, and the warning message
points you at `cache_bust_key_fn` as the fix.

## Async runner

`langgraph_runner`'s synchronous `graph.invoke()` path cannot reach bugs
that only manifest under a sustained async event loop -- e.g. a shared async
batch queue getting permanently poisoned by a cancelled future while other
concurrent callers are still waiting on it. `langgraph_async_runner` wraps
`graph.ainvoke()` instead, for use with
`agent_regress.core.runner.arun_suite()` and
`agent_regress.core.runner.concurrent_cancellation_probe()`:

```python
from agent_regress.core.runner import arun_suite
from agent_regress.integrations.langgraph import langgraph_async_runner

agent = langgraph_async_runner(graph)
scores = await arun_suite(agent, test_suite, n_runs=50, scorer=scorer)
```

`arun_suite` bounds total in-flight calls across *all* test cases and runs
with `max_concurrency=`, and mirrors `run_suite(..., stateful=True)`'s
per-test-case sequential guarantee when you pass `stateful=True` (needed for
a thread/session-aware graph accumulating state across one test case's
`n_runs` loop):

```python
scores = await arun_suite(
    agent, test_suite, n_runs=50, scorer=scorer, max_concurrency=8, stateful=True
)
```

For probing concurrency/cancellation liveness bugs directly -- firing many
concurrent calls against one shared test case and cancelling a fraction of
them mid-flight -- use `concurrent_cancellation_probe`:

```python
from agent_regress.core.runner import concurrent_cancellation_probe

result = await concurrent_cancellation_probe(
    agent, test_case, n_concurrent=20, cancel_fraction=0.3
)
# {"completed": 14, "cancelled": 6, "failed": 0}
```

### Store wiring (best-effort)

LangGraph wires a compiled graph's store in at compile time
(`graph.compile(store=...)`), not at invoke time -- there is no documented
`store=` keyword on `.invoke()`/`.ainvoke()`. `langgraph_async_runner`
accepts a `store=` parameter for convenience, but since there is no confirmed
runtime-injection kwarg to forward it to, it never silently drops it: it
stashes `store` under `config["configurable"]["store"]` on every call, so a
custom node function can read it back via `config["configurable"]["store"]`,
or a caller can inspect it after the fact:

```python
agent = langgraph_async_runner(graph, store=my_store)
```

If your compiled graph does support a genuine store kwarg on `.ainvoke()` in
your installed LangGraph version, prefer wiring the store in at compile time
instead of relying on this passthrough.
