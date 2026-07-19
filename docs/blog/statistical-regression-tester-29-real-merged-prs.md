# I built a statistical regression tester for AI agents, then tried to break it with 29 real merged pull requests

Co-authored by [Rudrendu Paul](https://dev.to/rudrendu_paul) and [Sourav Nandy](https://dev.to/sourav-nandy).

Repo: **[github.com/RudrenduPaul/agent-eval](https://github.com/RudrenduPaul/agent-eval)**. Star it if any of this is useful, the rest of this post is the receipts for why.

**TL;DR:** Most AI agent eval tools tell you whether one response cleared a threshold, not whether the agent's actual behavior changed between versions. I built `agent-eval` to answer that with a p-value and an effect size, then validated it against 239 real merged PRs from LangGraph, CrewAI, and the OpenAI Agents SDK, and it crashed on the first one. Here's what broke, what I fixed, and the 29 real PRs it's now proven against.

This is what a caught regression actually looks like, straight from the repo's own example running live:

![Terminal running the agent-eval basic-comparison example and printing a REGRESSED verdict with p-value 0.0000, Cohen's d -1.242, and a 95% CI that excludes zero](https://raw.githubusercontent.com/RudrenduPaul/agent-eval/main/docs/assets/demo-1-comparison.gif?v=2)

*The core value in one glance: `agent-eval` running 500 real trials per version and reporting a statistically confident REGRESSED verdict, not just a lower score.*

Gartner expects more than 40% of agentic AI projects to be scrapped by the end of 2027, and the reason cited most often is "escalating costs, unclear business value, or inadequate risk controls" ([Gartner, June 2025](https://www.gartner.com/en/newsroom/press-releases/2025-06-25-gartner-predicts-over-40-percent-of-agentic-ai-projects-will-be-canceled-by-end-of-2027)). Underneath "inadequate risk controls" is usually a simpler failure: nobody can tell whether the agent's behavior actually changed after the last deploy. A prompt tweak, a model swap from GPT-4o to a cheaper tier, a silent dependency bump in LangGraph or CrewAI, and the eval suite still shows green. That's because most eval suites check whether one response cleared a threshold. They don't check whether the whole distribution of behavior shifted.

That's the gap `agent-eval` (package name `agent_regress`) is built for: run an agent 50 times on version A, 50 times on version B, and report a p-value and an effect size on whether anything actually changed. I didn't want to just ship that and call it done. I wanted to know if it held up against real, merged, contested code changes from the frameworks people actually run agents on. So I took 239 real GitHub PRs from LangGraph, CrewAI, and the OpenAI Agents SDK, and for each one asked: if I pointed `agent-eval` at exactly this kind of change, would it deliver what a cold pitch about it would claim? What follows is what that campaign found, including the part where my own tool crashed on the first call.

## Why "the score looks different" isn't the same as "it regressed"

Most eval tools answer one question: did this response pass? DeepEval, Promptfoo, and Braintrust are all built around thresholds, a rubric score, an exact match, a judge-model verdict, and none of them tell you whether an agent's behavior meaningfully shifted between two versions of the same system. A 3-point accuracy drop between v1 and v2 might be real. It might also be ordinary LLM sampling variance. Without a distributional test you can't tell the difference, so teams either ignore small drops and eat the risk, or escalate everything and drown their on-call rotation in false alarms.

`agent-eval` answers the distributional question directly:

```python
from agent_regress import compare

report = compare(
    version_a=agent_v1,
    version_b=agent_v2,
    test_suite=test_suite,
    n_runs=50,
    metric="tool_accuracy",
)

print(report)
report.assert_stable()  # raises AssertionError if behavior regressed
```

Three statistical tools do the actual work. Mann-Whitney U compares the two score distributions without assuming they're normal, which matters because LLM output scores usually aren't. A bootstrap confidence interval (1,000 resamples) adds magnitude to that significance call: how large the shift actually was. Cohen's d then separates "statistically significant" from "operationally significant": a shift at p = 0.001 with d = 0.04 is real and irrelevant, a shift at p = 0.06 with d = 0.5 is large and needs more samples to confirm. The default CI gate only fires when both p < 0.05 and d ≥ 0.2, specifically so a 50-run comparison doesn't fail your build over noise.

None of that is exotic. The core call is one line of scipy, and I'll say that plainly because it matters for where this tool actually earns its keep. Any eval platform could bolt those statistics on in an afternoon. What's harder to copy is the version-specific regression history and the framework integrations that make the statistics reachable from a real agent, in CI, without hand-rolling a harness every time. It's also what turns "we swapped to a cheaper model to cut cost" from a leap of faith into a testable claim: a REGRESSED verdict with a p-value and a Cohen's d attached either backs that decision or kills it before it ships.

## The bug that would have crashed every single comparison

Here's where the story stops being a features list. Before I trusted the framework integrations enough to write outreach copy about them, I ran a validation pass: take a real, merged PR from LangGraph, CrewAI, or the OpenAI Agents SDK, and check whether `agent-eval`, as it existed in the repo that day, could actually produce the comparison a pitch about that PR would claim.

The very first thing that fell out was a P0. `openai_agents_runner()` called `agent.run(query)`. That method does not exist on the real SDK's `Agent` class, only `Runner.run(agent, input)` does. I confirmed it directly: `hasattr(agents.Agent(...), 'run')` returns `False`, `hasattr(agents.Runner, 'run')` returns `True`. That meant the integration raised `AttributeError` on its first call, for any test suite, any agent, any claim: a hard crash that took the whole integration down. It accounted for 15 of the 29 code-fixable gaps the campaign found, 51.7% of all of them, from one wrong method name.

Here's that exact crash, reproduced live against the real, currently installed OpenAI Agents SDK, running the actual pre-fix code straight from the commit history:

![Terminal running the pre-fix openai_agents_runner() against a real OpenAI Agents SDK Agent, ending in a real traceback: AttributeError: 'Agent' object has no attribute 'run'](https://raw.githubusercontent.com/RudrenduPaul/agent-eval/main/docs/assets/demo-2-p0-crash.gif?v=2)

*Not a mockup: this is the real buggy call site from the commit before the fix, executed against the real SDK, producing the real AttributeError that broke every comparison.*

I fixed the call site, then kept going, because a crash that big rarely travels alone. It didn't: `langgraph_runner()` built a fresh, stateless dict on every call with no `thread_id` and no checkpoint continuity, so it couldn't represent multi-turn conversations at all. `crewai_runner()` only wrapped a full `Crew.kickoff()`, with no way to isolate one tool's behavior. `run_suite()` had no cache-busting nonce, so any framework with its own persistent result cache (LangGraph's `cache_policy` is a real example) would silently collapse the repeated-sampling variance the whole statistical approach depends on. That last one turned into a second bug on inspection: a piece of state-narrowing logic downstream was dropping the cache-bust key I added. Re-review caught it; the first pass missed it.

Two commits closed all of it: [`bf3f46a`](https://github.com/RudrenduPaul/agent-eval/commit/bf3f46a) fixed the P0 and 16 other gaps, taking the test suite from 121 tests to 264 passing. [`146f064`](https://github.com/RudrenduPaul/agent-eval/commit/146f064) closed 7 more residual gaps that a second, independent re-validation pass surfaced, including an async cancellation liveness bug in the store layer.

The part worth naming explicitly, because it's the kind of thing you only learn by actually running an adversarial check instead of trusting your own fix: both passes independently caught the identical mistake on the first attempt, a proposed fix crediting code that was technically correct but still sitting uncommitted in the working tree. Twice. That's a specific, repeatable failure mode of self-reported "this is fixed now" claims, and it's why the validation methodology below runs every verdict through a propose-then-refute step instead of taking the first answer.

## 29 real merged PRs, and what it took to actually test them

Here's the part that matters more than any of the statistics: I anchored every fix above on a real, merged pull request. The full validation set covered 239 rows across six repos; 209 of those were correctly excluded because the underlying PR never carried the kind of behavioral-drift risk the pitch assumed, docs-only changes, trivial fixes, or PRs that plain didn't exist. Of the 29 rows where the code gap was real and fixable, all 29 now pass. One additional row (`@sibblegp`) has its code gap fully closed too, but stays below PASS for a reason no amount of engineering fixes: there's no genuine merged PR to anchor the claim on.

Here's a representative slice of those 29, spanning all three frameworks and most of the fix categories above:

| PR | Repo | What it changed | What `agent-eval` needed to test it |
|---|---|---|---|
| [langgraph #5243](https://github.com/langchain-ai/langgraph/pull/5243) | LangGraph | New typed `context=` API, replacing untyped `config['configurable']` | `langgraph_runner()` gained `config`, `context`, and `thread_aware` kwargs so both invocation styles compare directly |
| [openai-agents-python #2463](https://github.com/openai/openai-agents-python/pull/2463) | OpenAI Agents SDK | Fixed agent-as-tool silently dropping the parent run's `RunConfig` | Fixed the P0 crash, then added `capture_trace=` telemetry so RunConfig inheritance is observable per nested call |
| [crewAI #6236](https://github.com/crewAIInc/crewAI/pull/6236) | CrewAI | Optional Pydantic `output_schema` on tools, structured JSON instead of `str()` | New `crewai_tool_runner()` isolates a single tool, plus a `schema_conformance_scorer()` |
| [langgraph #7746](https://github.com/langchain-ai/langgraph/pull/7746) | LangGraph | Reworked checkpoint snapshot cadence to key on supersteps, not just updates | `thread_aware=True` for per-case thread continuity across repeated runs |
| [crewAI #6134](https://github.com/crewAIInc/crewAI/pull/6134) | CrewAI | Security fix: file tools were leaking absolute filesystem paths in responses | New `no_path_leak_scorer()` flags raw paths in tool-response text |
| [openai-agents-python #2214](https://github.com/openai/openai-agents-python/pull/2214) | OpenAI Agents SDK | Stopped image/audio/file tool outputs from being silently dropped to text-only | `capture_trace=` intercepts the SDK's real conversion function directly, so regressions of this exact class are now detectable |
| [langgraph #3126](https://github.com/langchain-ai/langgraph/pull/3126) | LangGraph | Reworked `ToolNode` dispatch, risking duplicate tool calls on interrupt/resume | `tool_call_trace_scorer()` plus a real `langgraph_interrupt_resume_runner()` that drives an actual interrupt-then-resume cycle |
| [openai-agents-python #2902](https://github.com/openai/openai-agents-python/pull/2902) | OpenAI Agents SDK | Added a persistent MongoDB session backend for multi-turn continuity | `session_aware=True` reuses one session per logical test case instead of building a fresh one every call |
| [langgraph #4486](https://github.com/langchain-ai/langgraph/pull/4486) | LangGraph | Added node/task-level result caching, which can mask repeated-sampling variance | `cache_bust_key_fn()` plus `graph_has_cache()`, and the dropped-nonce bug described above |
| [langgraph #6701](https://github.com/langchain-ai/langgraph/pull/6701) | LangGraph | Fixed a cancelled-future re-queue bug in the async batching store layer | New `arun_suite()`, `langgraph_async_runner()`, and `concurrent_cancellation_probe()` to reach async liveness bugs at all |
| [openai-agents-python #2328](https://github.com/openai/openai-agents-python/pull/2328) | OpenAI Agents SDK | Fixed a hard crash using DeepSeek's thinking mode through LiteLLM | Fixed the P0 crash; verified end-to-end against a live install |
| [crewAI #6079](https://github.com/crewAIInc/crewAI/pull/6079) | CrewAI | Four pluggable storage backends for memory, knowledge, RAG, and flow persistence | `crew_factory=` builds a fresh `Crew` per invocation, avoiding shared-mutable-state corruption under concurrent comparison |
| [crewAI #4446](https://github.com/crewAIInc/crewAI/pull/4446) | CrewAI | Substantial refactor of the Brave Search tool integration | `subprocess_runner()` compares `crewai-tools` versions pre- and post-PR |
| [openai-agents-python #1744](https://github.com/openai/openai-agents-python/pull/1744) | OpenAI Agents SDK | Added support for Anthropic's extended/interleaved thinking via LiteLLM | Fixed the P0 crash, closing the runner-level failure that blocked exercising this feature at all |

Every link above resolves to a real, merged PR. The pattern across all 29 is the same one: the plumbing connecting `agent-eval`'s statistics to a specific framework's real API surface was incomplete, and that only became visible by testing against what maintainers had actually shipped.

## Where this sits next to DeepEval, Promptfoo, and Braintrust

The eval space isn't short on tools, and it's consolidating. OpenAI [acquired Promptfoo in March 2026](https://openai.com/index/openai-to-acquire-promptfoo/), keeping it open-source but folding its team in-house, a signal that the eval layer now counts as load-bearing infrastructure. DeepEval and Braintrust remain strong at what they're built for: did this response clear a rubric, an exact match, a judge-model score. None of the three report a p-value, an effect size, or a bootstrap confidence interval on whether behavior shifted between two versions, because that's a different statistical question than the one they're built to answer.

That distinction matters more as the ecosystem this operates in keeps growing. LangGraph alone is at 37,447 GitHub stars and roughly 66.7 million PyPI downloads a month as of this writing, CrewAI at 55,648 stars and about 11.3 million downloads a month. That's a lot of production agents changing versions on a normal release cadence, and threshold evals genuinely cannot tell you, on their own, whether any given release actually changed real behavior or just changed the score.

## What this campaign didn't prove, on purpose

I'd rather state the limits plainly than let the 29-for-29 number imply more than it does. Of the 239 rows in the full validation set, I excluded 209 (87.4%) simply because the pitch itself didn't apply to those PRs. That's a very different claim from "29 out of 239 attempts succeeded." That distinction also means this campaign says nothing about `agent-eval`'s coverage of frameworks like AutoGen (still on the roadmap) or about correctness questions the stats module was never meant to answer, like whether a scorer function itself is well-designed. And the honest caveat from the README stands: the statistical core is one `scipy.stats.mannwhitneyu` call. Any SaaS eval platform could add it in an afternoon if they decided the distributional question was worth answering. The framework-specific plumbing doesn't come free: this campaign spent two commits building and re-testing it. The version-specific regression history only accumulates from real use.

## There's a CLI now too, built for scripts and agents, not just Python imports

`agent-eval` shipped as a pure Python import for its first several months. As of this week, it's also a real CLI:

```bash
pip install agent-regress-cli
# or, via npx if you'd rather not touch Python directly
npx agent-regress-npm-cli --help
```

The Python API's `compare()` takes two callables and runs them itself, a shape that has no clean command-line equivalent. So the CLI starts one step later: it takes two JSON files, each a flat array of per-run scores your own harness already computed, and runs them through the same Mann-Whitney U, bootstrap CI, and Cohen's d pipeline the Python API uses internally:

```bash
agent-regress compare \
  --version-a-results v1_scores.json \
  --version-b-results v2_scores.json \
  --metric tool_accuracy \
  --json \
  --fail-on-regression
```

`--json` prints a single, parseable JSON object to stdout and routes warnings to stderr, so stdout stays clean. The CLI's own source calls this "the agent-native machine-readable surface": a report an orchestration script, a CI job, or another agent can consume directly instead of scraping human-formatted text. `--fail-on-regression` exits 1 on a REGRESSED verdict, so the same command drops straight into a CI gate.

![Terminal running agent-regress compare on two JSON score files and printing a REGRESSED verdict with p-value, Cohen's d, and confidence interval](https://raw.githubusercontent.com/RudrenduPaul/agent-eval/main/docs/assets/demo-3-cli.gif?v=2)

*The finished state: two pre-computed score files in, a full statistical verdict out, no Python required.*

## Try it against your own agent

```python
from agent_regress import compare, RegressionGate

gate = RegressionGate(p_threshold=0.05, min_effect=0.2)

def test_tool_accuracy():
    report = compare(version_a=prod_agent, version_b=staging_agent, test_suite=suite, n_runs=50)
    gate.check(report)  # raises AssertionError on regression, warns if n < 30
```

Framework integrations for LangGraph, the OpenAI Agents SDK, CrewAI, and LangChain LCEL ship today. I measured statistical overhead on an M3 Pro at about 27ms per comparison at n=50; the agent calls themselves stay the real bottleneck, the math barely registers. Apache 2.0, self-hostable, no SaaS account required. `docker compose up` gets you a working example and the leaderboard UI in one command if you want to see it running before wiring it into anything.

If you maintain or contribute to LangGraph, CrewAI, or the OpenAI Agents SDK, there's a decent chance one of your own merged PRs is hiding in that 239-row dataset. The good-first-issues list is open if you want to help close the remaining gaps.

One thing I haven't decided yet: the next release either adds AutoGen support or spends that time deepening CI ergonomics for the three frameworks already shipped (a native GitHub Actions annotation format, a richer `--json` schema for dashboards). Which would you actually use, and if you maintain an agent framework I haven't covered, what does your regression suite still miss?

Repo again: **[github.com/RudrenduPaul/agent-eval](https://github.com/RudrenduPaul/agent-eval)**. If this saved you from shipping a silent regression, or just made you distrust your own eval suite a little more than you did five minutes ago, a star helps other people building agents find it before they need it.

---

### References

- Gartner, ["Gartner Predicts Over 40% of Agentic AI Projects Will Be Canceled by End of 2027"](https://www.gartner.com/en/newsroom/press-releases/2025-06-25-gartner-predicts-over-40-percent-of-agentic-ai-projects-will-be-canceled-by-end-of-2027), June 25, 2025
- OpenAI, ["OpenAI to acquire Promptfoo"](https://openai.com/index/openai-to-acquire-promptfoo/), March 9, 2026
- GitHub and PyPI star/download counts self-reported via public API as of July 16, 2026

*Rudrendu Paul builds open-source developer tools for the AI agent ecosystem. He is the co-author of [agent-eval](https://github.com/RudrenduPaul/agent-eval) (`agent-regress`), a statistical regression-testing library for LLM agents, and spent the past several months validating it against real merged PRs in LangGraph, CrewAI, and the OpenAI Agents SDK.*
