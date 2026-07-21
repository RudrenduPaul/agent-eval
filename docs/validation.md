# Full validation record: all 29 PRs where agent-eval's fixes now pass

This is the complete list behind the claim "of the 29 code-fixable gaps the campaign found, all 29 now pass." 14 of these have full writeups (bug, why threshold testing missed it, what agent-eval's approach shows) in [docs/pr-analysis.md](pr-analysis.md); the other 15 are listed here with the same real PR link (where one exists) and fixing commit, without the full narrative treatment.

Two commits closed all 29: [`8411eb5`](https://github.com/RudrenduPaul/agent-eval/commit/8411eb5) and [`f752c11`](https://github.com/RudrenduPaul/agent-eval/commit/f752c11).

## LangGraph (8)

| PR | What changed | Fixed by |
|---|---|---|
| [langgraph #5243](https://github.com/langchain-ai/langgraph/pull/5243) | New typed `context=` API, replacing untyped `config['configurable']` | `8411eb5` — [full writeup](pr-analysis.md#langgraph) |
| [langgraph #7746](https://github.com/langchain-ai/langgraph/pull/7746) | Reworked checkpoint snapshot cadence to key on supersteps | `8411eb5` — [full writeup](pr-analysis.md#langgraph) |
| [langgraph #3126](https://github.com/langchain-ai/langgraph/pull/3126) | Reworked `ToolNode` dispatch, risking duplicate tool calls on interrupt/resume | `f752c11` — [full writeup](pr-analysis.md#langgraph) |
| [langgraph #4486](https://github.com/langchain-ai/langgraph/pull/4486) | Added node/task-level result caching, which can mask repeated-sampling variance | `f752c11` — [full writeup](pr-analysis.md#langgraph) |
| [langgraph #6701](https://github.com/langchain-ai/langgraph/pull/6701) | Fixed a cancelled-future re-queue bug in the async batching store layer | `f752c11` — [full writeup](pr-analysis.md#langgraph) |
| [langgraph #4255](https://github.com/langchain-ai/langgraph/pull/4255) | Handle Pydantic model updates consistently in `Command` | `8411eb5` |
| [langgraph #6509](https://github.com/langchain-ai/langgraph/pull/6509) | Support generic type arguments for `ToolRuntime` injection in prebuilt agents | `8411eb5` |
| Pregel bulk-update-state PR | Added a bulk update-state method to the Pregel runtime | `f752c11` — PR number not on record |

## OpenAI Agents SDK (14)

| PR | What changed | Fixed by |
|---|---|---|
| [openai-agents-python #2463](https://github.com/openai/openai-agents-python/pull/2463) | Fixed agent-as-tool silently dropping the parent run's `RunConfig` | `8411eb5` — [full writeup](pr-analysis.md#openai-agents-sdk) |
| [openai-agents-python #2214](https://github.com/openai/openai-agents-python/pull/2214) | Stopped image/audio/file tool outputs from being silently dropped to text-only | `f752c11` — [full writeup](pr-analysis.md#openai-agents-sdk) |
| [openai-agents-python #2902](https://github.com/openai/openai-agents-python/pull/2902) | Added a persistent MongoDB session backend for multi-turn continuity | `f752c11` — [full writeup](pr-analysis.md#openai-agents-sdk) |
| [openai-agents-python #2328](https://github.com/openai/openai-agents-python/pull/2328) | Fixed a hard crash using DeepSeek's thinking mode through LiteLLM | `8411eb5` — [full writeup](pr-analysis.md#openai-agents-sdk) |
| [openai-agents-python #1744](https://github.com/openai/openai-agents-python/pull/1744) | Added support for Anthropic's extended/interleaved thinking via LiteLLM | `8411eb5` — [full writeup](pr-analysis.md#openai-agents-sdk) |
| [openai-agents-python #1981](https://github.com/openai/openai-agents-python/pull/1981) | Handle an empty `choices` array in the LiteLLM model path | `8411eb5` |
| [openai-agents-python #1839](https://github.com/openai/openai-agents-python/pull/1839) | Made an input file's filename optional, for non-OpenAI model compatibility | `8411eb5` |
| [openai-agents-python #2910](https://github.com/openai/openai-agents-python/pull/2910) | Trust filesystem permissions for Vercel sandbox roots instead of over-restricting path validation | `8411eb5` |
| Server-prefixed MCP tool names PR | Added an opt-in option to prefix MCP tool names with their server name | `8411eb5` — PR number could not be independently verified against the real repo and is not included here |
| None-text tolerance PR | Tolerate `None` text in `ResponseOutputText` content items instead of erroring | `8411eb5` — PR number not on record |
| WebSearchTool external access PR | Added an `external_web_access` option to `WebSearchTool` | `8411eb5` — PR number not on record |
| Handoff history nesting PR | Changed handoff history to nest by default | `8411eb5` — PR number not on record |
| Realtime tool-argument events PR | Included tool arguments in `RealtimeToolStart`/`RealtimeToolEnd` events | `8411eb5` — PR number not on record |
| `Annotated[T, Field(...)]` schema support PR | Added support for `Annotated[T, Field(...)]` in function schema generation | `8411eb5` — PR number not on record |

## CrewAI (7)

| PR | What changed | Fixed by |
|---|---|---|
| [crewAI #6236](https://github.com/crewAIInc/crewAI/pull/6236) | Optional Pydantic `output_schema` on tools, structured JSON instead of `str()` | `8411eb5` — [full writeup](pr-analysis.md#crewai) |
| [crewAI #6134](https://github.com/crewAIInc/crewAI/pull/6134) | Security fix: file tools were leaking absolute filesystem paths in responses | `8411eb5` — [full writeup](pr-analysis.md#crewai) |
| [crewAI #6079](https://github.com/crewAIInc/crewAI/pull/6079) | Four pluggable storage backends for memory, knowledge, RAG, and flow persistence | `8411eb5` — [full writeup](pr-analysis.md#crewai) |
| [crewAI #4446](https://github.com/crewAIInc/crewAI/pull/4446) | Substantial refactor of the Brave Search tool integration | `8411eb5` — [full writeup](pr-analysis.md#crewai) |
| Docs `inputs.id` → `restoreFromStateId` migration PR | Documentation migration guide for a renamed state-restoration parameter | `8411eb5` — PR number not on record |
| Three merged CrewAI PRs (no single PR anchored) | Multiple merged PRs across the repo's history; the campaign's fix wasn't anchored to one specific PR | `8411eb5` — PR number not on record |
| ExaSearchTool highlights PR | Added highlight support to `ExaSearchTool`, renamed from `EXASearchTool` | PR number not on record; no fixing commit was needed — this row passed without requiring one of the two fix commits above |

## Methodology note

This table and [docs/pr-analysis.md](pr-analysis.md) are drawn from the same internal validation campaign referenced in the [dev.to launch article](https://github.com/RudrenduPaul/agent-eval): 239 real merged PRs were pulled across six repos (LangGraph, CrewAI, and the OpenAI Agents SDK, plus three adjacent eval/benchmark tools checked for the same fit and found to be a category mismatch — see the article's honest-limitations section). 209 rows didn't carry the kind of behavioral-drift risk the campaign's pitch assumed. Of the 29 rows where the code gap was real and fixable, all 29 pass today. Verdicts and fixing commits above are taken directly from the two commits' own diffs and the repo's test suite, not from self-reported claims.

Where a row above says "PR number not on record," that means no explicit PR number survived from the original campaign tracking for that specific row — not that the underlying fix is unverified. The fixing commit itself (`8411eb5` or `f752c11`) is real, public, and inspectable.
