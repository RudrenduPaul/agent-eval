# PR Analysis: real regressions statistical testing catches that threshold testing misses

This is the full detail behind the README's "Real regressions statistical testing catches that threshold testing misses" section: for each PR below, what actually changed, why a single-response threshold check would have cleared it anyway, and what `agent-eval`'s distributional/statistical approach shows instead.

## LangGraph

### [langgraph #5243](https://github.com/langchain-ai/langgraph/pull/5243) — New typed `context=` API, replacing untyped `config['configurable']`
**Bug:** LangGraph replaced the untyped `config['configurable']` dict-based way of passing per-invocation state into the graph with a new typed `context=` API, a breaking change to how callers supply that state.
**Why threshold testing missed it:** A single test run using either the old or the new invocation style still produces a plausible-looking response that clears a threshold check. The incompatibility only shows up as a difference in behavior between the two invocation paths, not as an outright failure on either one alone.
**What agent-eval's approach shows:** `langgraph_runner()` gained `config`, `context`, and `thread_aware` kwargs so both invocation styles can be run as version A and version B distributions, letting a comparison report whether the switch actually changed measured behavior rather than just confirming either style "worked."

### [langgraph #7746](https://github.com/langchain-ai/langgraph/pull/7746) — Reworked checkpoint snapshot cadence to key on supersteps, not just updates
**Bug:** LangGraph changed when checkpoint snapshots are taken, keying on supersteps instead of every update, which changes what state is visible or recoverable at each point in a multi-turn run.
**Why threshold testing missed it:** A single-turn or single-snapshot check still returns a fine-looking result. The regression only appears in multi-turn continuity, where the wrong snapshot cadence causes state to be missing or stale across turns, a code path a one-shot threshold test never exercises.
**What agent-eval's approach shows:** `thread_aware=True` gives `agent-eval` per-case thread continuity across repeated runs, so it can detect a measurable behavioral drift over a multi-turn conversation caused by a checkpoint-cadence change, not just single-call correctness.

### [langgraph #3126](https://github.com/langchain-ai/langgraph/pull/3126) — Reworked `ToolNode` dispatch, risking duplicate tool calls on interrupt/resume
**Bug:** A rework of `ToolNode` dispatch introduced a risk of duplicate tool calls specifically when a run is interrupted and then resumed.
**Why threshold testing missed it:** A single end-to-end run without an interrupt/resume cycle never touches the code path where duplication happens, so a threshold test on a plain run looks completely fine even though the interrupt/resume path is broken.
**What agent-eval's approach shows:** A real `langgraph_interrupt_resume_runner()` drives an actual interrupt-then-resume cycle, and `tool_call_trace_scorer()` can statistically detect duplicate tool calls appearing across repeated runs, a regression class a non-interrupting test would never see.

### [langgraph #4486](https://github.com/langchain-ai/langgraph/pull/4486) — Added node/task-level result caching, which can mask repeated-sampling variance
**Bug:** LangGraph added node/task-level result caching, which can cause repeated calls to return a cached result instead of a freshly computed one.
**Why threshold testing missed it:** A single-response threshold check doesn't care whether a result came from cache or was freshly computed, so caching that silently collapses repeated-sampling variance is invisible to it, and it directly undermines any method that depends on genuinely independent repeated samples.
**What agent-eval's approach shows:** `cache_bust_key_fn()` and `graph_has_cache()` ensure `agent-eval`'s repeated runs aren't silently served from cache, preserving the independent-sample assumption the statistical comparison depends on. This also surfaced a second, related dropped-nonce bug in `agent-eval`'s own state-narrowing logic that only a second, independent re-validation pass caught.

### [langgraph #6701](https://github.com/langchain-ai/langgraph/pull/6701) — Fixed a cancelled-future re-queue bug in the async batching store layer
**Bug:** A cancelled-future re-queue bug in the async batching store layer could leave the system in a bad liveness state under cancellation.
**Why threshold testing missed it:** This is an async concurrency/liveness bug that only manifests under cancellation timing. A synchronous, single-shot threshold test never triggers cancellation at all, so the bug is structurally invisible to that kind of test.
**What agent-eval's approach shows:** New `arun_suite()`, `langgraph_async_runner()`, and `concurrent_cancellation_probe()` give `agent-eval` a way to actually reach async liveness bugs. Without an async-aware, cancellation-probing runner, this regression class can't be tested at all, regardless of statistical method.

## OpenAI Agents SDK

### [openai-agents-python #2463](https://github.com/openai/openai-agents-python/pull/2463) — Fixed agent-as-tool silently dropping the parent run's `RunConfig`
**Bug:** When one agent is used as a tool by another agent, the parent run's `RunConfig` (tracing/model settings and similar) was being silently dropped instead of inherited by the nested call.
**Why threshold testing missed it:** The nested agent call still returns a normal-looking response even without the inherited `RunConfig`, so a single-response threshold check clears; the regression is invisible unless something actually inspects whether config propagated.
**What agent-eval's approach shows:** `capture_trace=` telemetry makes `RunConfig` inheritance observable per nested call, so a version comparison can detect a distributional shift when inheritance silently breaks, not just confirm that the outer call returns a response. (This is also one of the 15 gaps traced back to the P0 bug, where `openai_agents_runner()` called a nonexistent `agent.run()` and had to be fixed before any of this could be tested.)

### [openai-agents-python #2214](https://github.com/openai/openai-agents-python/pull/2214) — Stopped image/audio/file tool outputs from being silently dropped to text-only
**Bug:** Tool outputs containing image, audio, or file content were being silently downgraded to text-only, dropping the non-text payload.
**Why threshold testing missed it:** A text-based threshold or rubric check only ever looks at the text portion of a response, so it has no way to notice that an image or audio attachment was silently dropped — the text can still look complete and correct.
**What agent-eval's approach shows:** `capture_trace=` intercepts the SDK's real conversion function directly, so `agent-eval` can observe when multimodal tool outputs get silently downgraded to text and detect that class of regression across a version comparison, not just eyeball the text response.

### [openai-agents-python #2902](https://github.com/openai/openai-agents-python/pull/2902) — Added a persistent MongoDB session backend for multi-turn continuity
**Bug:** Added a new persistent, MongoDB-backed session backend intended to preserve multi-turn conversational continuity.
**Why threshold testing missed it:** If every test call builds a fresh session instead of reusing one, the continuity feature is never actually exercised, so a threshold check on isolated single-turn responses can't observe whether session persistence works or regresses.
**What agent-eval's approach shows:** `session_aware=True` reuses one session per logical test case instead of building a fresh one every call, so `agent-eval` can measure whether multi-turn continuity actually holds, or regresses, across versions using the real persistent backend.

### [openai-agents-python #2328](https://github.com/openai/openai-agents-python/pull/2328) — Fixed a hard crash using DeepSeek's thinking mode through LiteLLM
**Bug:** Using DeepSeek's thinking mode through LiteLLM caused a hard crash in the OpenAI Agents SDK integration.
**Why threshold testing missed it:** A hard crash is the one failure mode a threshold test would normally catch, but only if the test harness can reach that code path at all. `agent-eval`'s own runner had the P0 bug (`agent.run()` didn't exist) blocking every call before this fix, so no comparison could even be attempted until that was fixed.
**What agent-eval's approach shows:** With the P0 crash fixed and verified end-to-end against a live install, `agent-eval`'s runner can actually execute this code path, making the statistical comparison possible in the first place. This fix enables testing this regression class at all, rather than refining an existing detection.

### [openai-agents-python #1744](https://github.com/openai/openai-agents-python/pull/1744) — Added support for Anthropic's extended/interleaved thinking via LiteLLM
**Bug:** Added support for Anthropic's extended/interleaved thinking mode via LiteLLM, a new capability path through the SDK.
**Why threshold testing missed it:** Before the P0 fix, `agent-eval`'s runner couldn't execute any call against the SDK at all, `agent.run()` didn't exist. This isn't a case of a threshold test looking at the wrong signal; it's the more basic failure of not being able to run any test against this feature in the first place.
**What agent-eval's approach shows:** Fixing the P0 crash closed the runner-level failure that blocked exercising this feature entirely, meaning `agent-eval` can now run comparisons against extended-thinking-enabled calls. Statistical detection of behavioral drift on this capability is possible only because the runner works now.

## CrewAI

### [crewAI #6236](https://github.com/crewAIInc/crewAI/pull/6236) — Optional Pydantic `output_schema` on tools, structured JSON instead of `str()`
**Bug:** Tools gained an optional Pydantic `output_schema`, switching their output from an unstructured `str()` dump to structured JSON, a format change downstream consumers depend on.
**Why threshold testing missed it:** A threshold or rubric scorer judging "is this a reasonable-looking tool response" passes both the old string output and the new JSON output, since both can look correct to a judge model even though the underlying schema is different.
**What agent-eval's approach shows:** The new `crewai_tool_runner()` isolates a single tool's output instead of the whole `Crew.kickoff()`, and `schema_conformance_scorer()` can statistically flag when tool output stops conforming to the expected schema across repeated runs.

### [crewAI #6134](https://github.com/crewAIInc/crewAI/pull/6134) — Security fix: file tools were leaking absolute filesystem paths in responses
**Bug:** File-handling tools were leaking absolute filesystem paths into their responses, a security-relevant information disclosure.
**Why threshold testing missed it:** A quality or accuracy threshold scorer checks whether the response answers the task correctly, not whether it also happens to contain a leaked filesystem path; a response can be "correct" and still leak the path, so it clears the bar.
**What agent-eval's approach shows:** The new `no_path_leak_scorer()` specifically flags raw paths in tool-response text, letting a version comparison catch a regression where a code change reintroduces path leakage even if overall task-quality scores look unchanged.

### [crewAI #6079](https://github.com/crewAIInc/crewAI/pull/6079) — Four pluggable storage backends for memory, knowledge, RAG, and flow persistence
**Bug:** CrewAI added four pluggable storage backends for memory, knowledge, RAG, and flow persistence, replacing a more monolithic storage model.
**Why threshold testing missed it:** A single, sequential test run doesn't expose shared-mutable-state issues; those only appear under concurrent access, which a one-response-at-a-time threshold check never simulates.
**What agent-eval's approach shows:** `crew_factory=` builds a fresh `Crew` per invocation, avoiding shared-mutable-state corruption when `agent-eval` runs many comparisons concurrently, keeping the repeated-sampling comparisons statistically independent instead of letting them cross-contaminate each other's state.

### [crewAI #4446](https://github.com/crewAIInc/crewAI/pull/4446) — Substantial refactor of the Brave Search tool integration
**Bug:** A substantial refactor of the Brave Search tool integration changed its internal implementation, with a real risk of behavior drift even if the tool's basic "does it return search results" check still passes.
**Why threshold testing missed it:** A basic pass/fail check on "did the tool return something plausible" clears easily after a refactor, since the tool still nominally works, it just may behave differently (different result ranking, formatting, edge-case handling) than before.
**What agent-eval's approach shows:** `subprocess_runner()` compares `crewai-tools` versions pre- and post-PR directly, letting `agent-eval` statistically detect whether the refactor changed the tool's actual output distribution, not just whether it still returns "a result."

## Summary

These 14 PRs are the representative slice `agent-eval`'s own validation campaign publishes with individual PR links, drawn from the 29 real merged PRs (across LangGraph, CrewAI, and the OpenAI Agents SDK) that the campaign confirmed as real, fixable code gaps, all 29 now pass. That 29 sits inside a larger 239-row validation set spanning six repos, where 209 rows (87.4%) were correctly excluded because the underlying PR never carried the kind of behavioral-drift risk the pitch assumed, docs-only changes, trivial fixes, or PRs that didn't exist. The pattern across all 29 is the same one visible above: the plumbing connecting `agent-eval`'s statistics to a specific framework's real API surface was incomplete, and threshold testing's single-response pass/fail check had no way to see that, because the response in front of it still looked fine.
