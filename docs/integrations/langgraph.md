# LangGraph Integration

## Install

```bash
pip install agent-regress-cli[langgraph]
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

The `config` -> `context` migration itself (LangGraph PR #5243) is a risk
class worth regression-testing directly: platform-supplied values like
`thread_id`/`run_id` live in `config`, not in a user's `context_schema`, so a
node ported to `runtime.context` ahead of the rest of the call chain reads
`None` instead of raising -- a silent behavioral regression, not a crash. See
`examples/05-langgraph-context-api-migration/` for a `compare()` harness
that catches exactly this.

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

`langgraph_async_runner` takes the same `operation` parameter -- an async
`(graph, test_case) -> Awaitable[Any]` callable -- so async checkpoint-surgery
methods like `abulk_update_state` are reachable through
`arun_suite()`/`concurrent_cancellation_probe()` too, not just via the
synchronous runner:

```python
agent = langgraph_async_runner(
    graph,
    operation=lambda g, tc: g.abulk_update_state(tc["config"], tc["updates"]),
)
```

As with `langgraph_runner`, when `operation` is given, `input_key`/`store`/
`config`/`context` are ignored for that call.

## Interrupt / resume, checking for double-execution

`langgraph_runner`'s `operation=`/`thread_aware=` params already let you
hand-roll an interrupt-then-resume test, but for the common case -- "does a
node re-execute a tool call after a resume?" (the risk class behind
LangGraph PR #3126, "allow ToolNode to accept ToolCalls") -- use
`langgraph_interrupt_resume_runner`, a built-in convenience that does the
whole cycle for you:

```python
from agent_regress.integrations.langgraph import langgraph_interrupt_resume_runner
from agent_regress.core.scorer import tool_call_trace_scorer

agent = langgraph_interrupt_resume_runner(graph, resume_value="approved")

result = agent({"messages": [...], "expected_tool_call_ids": ["call-1", "call-2"]})
# result == {"result": <final invoke() return value>, "interrupted": bool,
#            "messages": <final result["messages"] if present, else None>}

score = tool_call_trace_scorer(result, test_case)
```

Per test case it: (1) calls `graph.invoke(state, config=call_config)` once,
with an auto-generated, per-test-case-stable `thread_id` injected into
`call_config["configurable"]["thread_id"]` (unless your `config=` already
supplies one); (2) calls `graph.get_state(call_config)` and checks whether
the graph actually paused at an `interrupt()` -- verified against the
installed LangGraph source (`langgraph.types.StateSnapshot`): non-empty
`.next`, non-empty `.interrupts`, or any task in `.tasks` with a non-empty
`.interrupts`; (3) if interrupted, resumes via
`graph.invoke(Command(resume=resume_value), config=call_config)` (`Command`
from `langgraph.types`); (4) returns the dict shown above. Because
`tool_call_trace_scorer` reads `output["messages"]` directly, you can pass
this dict straight to it as `output` -- if a tool node re-executed after
resume, the repeated `tool_call_id` scores below `1.0`.

If the input never triggers an `interrupt()`, step 3 is skipped and
`interrupted=False` comes back -- that's a real result, not an error. Only
one interrupt/resume cycle is exercised per call; a graph that interrupts
more than once will only have its first pause resumed.

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
SUT-side cache. Inject the nonce under the reserved `CACHE_BUST_NONCE_KEY`
constant (not an arbitrary key name) -- `langgraph_runner` and
`langgraph_async_runner` both special-case that exact key so it survives
`input_key` narrowing (see below) and still reaches the graph:

```python
import uuid

from agent_regress.core.runner import CACHE_BUST_NONCE_KEY, run_suite

def bust_cache(test_case: dict, run_index: int) -> dict:
    return {CACHE_BUST_NONCE_KEY: str(uuid.uuid4())}

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

**Why the reserved key matters:** both `langgraph_runner` and
`langgraph_async_runner` build the graph's input state by narrowing the test
case down to a single `input_key` field (e.g. `{"messages": ...}`) when that
key is present -- every other top-level key is dropped by design. Without a
predictable name to special-case, a `cache_bust_key_fn`-injected nonce would
be silently dropped by that same narrowing, defeating cache-busting entirely
for any test suite whose cases carry `input_key`. Both runners preserve
`CACHE_BUST_NONCE_KEY` specifically through the narrowing (alongside
`input_key`) so this failure mode can't happen as long as you inject the
nonce under that constant.

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

A single `concurrent_cancellation_probe()` call only gives you one batch's
counts, not a statistically-grounded verdict on whether a code change made
liveness under cancellation better or worse. `compare_liveness()` runs the
probe repeatedly against two agents and turns the resulting distributions
into a `Report`, the same way `compare()` does for scalar scores -- use it
to regression-test a queue/session liveness fix (e.g. a fix for a shared
async batch queue that used to get permanently poisoned by a cancelled
future) the same way you'd regression-test accuracy:

```python
from agent_regress.core.compare import compare_liveness
from agent_regress.integrations.langgraph import langgraph_async_runner

# graph_before: pre-fix build (susceptible to queue poisoning on cancellation)
# graph_after: post-fix build
agent_before = langgraph_async_runner(graph_before)
agent_after = langgraph_async_runner(graph_after)

report = await compare_liveness(
    agent_a=agent_before,
    agent_b=agent_after,
    test_case=test_case,
    n_concurrent=20,
    cancel_fraction=0.3,
    n_trials=30,
)
print(report)
```

Each trial reduces one `concurrent_cancellation_probe()` call to a single
liveness score, `completed / n_concurrent` -- the fraction of the batch
that finished successfully despite the injected cancellations. A queue that
gets permanently poisoned by a cancelled future drives this toward 0 even
for calls that were never themselves cancelled, so `agent_a`/`agent_b`
here play the same "baseline vs. candidate" role `version_a`/`version_b`
play in `compare()`: if the post-fix graph is reliably more live under
concurrent cancellation, `report.verdict` comes back `Verdict.IMPROVED`
(same p-value/effect-size thresholding and `INSUFFICIENT_DATA`-below-10
rule `compare()` uses); if a change to the graph regresses liveness,
you'll see `Verdict.REGRESSED` instead.

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
