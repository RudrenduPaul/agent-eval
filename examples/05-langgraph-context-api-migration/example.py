"""Example 05: LangGraph context API migration (PR #5243).

Case study for langchain-ai/langgraph#5243 ("new context api, replacing
config['configurable'] and config_schema"), authored by @sydney-runkle and
merged 2025-07-15. The PR itself documents the exact risk this example
probes:

  - sydney-runkle, on the PR: "Known issue that this is not fully
    compatible with `langgraph-api`. Will update `langgraph-api` to be
    backwards and forwards compat."
  - @albeiroespitia, on the PR, after the API shipped: "how do we get the
    thread_id and the run_id within the node? I used to get it with the
    config parameter but now the context does not include it."

Both are the same failure mode: `thread_id`/`run_id` used to be readable
from any node via `config["configurable"]`, unconditionally. After the
migration to `runtime.context`, those platform-supplied values are only
present if the caller's `context_schema` was updated to carry them --
`context` is meant for user-supplied static data, not
checkpointer/langgraph-api plumbing. A node ported to `runtime.context`
before the rest of the call chain (config, langgraph-api) catches up gets
a `None`/missing value instead of a loud failure, so nothing crashes and
nothing shows up in CI -- it just silently degrades whatever the node does
with that value (thread continuity, per-user memory namespacing, etc.).

That's precisely the gap agent-regress is built to close: a type-safe
refactor that never raises can still be a behavioral regression. This
example models version_a (pre-#5243, reading thread_id/user_id from
`config["configurable"]`, always present) against version_b (post-#5243,
reading them from `runtime.context`, present only for the fraction of
calls whose caller has finished migrating -- the rest silently get `None`),
and runs `compare()` to produce the artifact that would have flagged this
before merge instead of via a user bug report weeks after ship.

Run with: python examples/05-langgraph-context-api-migration/example.py
"""

from __future__ import annotations

import random
from typing import Any

from agent_regress import compare
from agent_regress.ci.gate import assert_no_regression

# Share of post-#5243 calls made through a caller (e.g. langgraph-api, or
# application code) that has NOT yet been migrated to pass thread_id/user_id
# via `context=` -- mirrors sydney-runkle's "not fully compatible with
# langgraph-api" comment. Not 100%: the break is partial and intermittent,
# which is exactly why it shipped and was only caught by users afterward.
UNMIGRATED_CALLER_RATE = 0.35


def pre_5243_agent(test_case: dict[str, Any]) -> str:
    """Node reads config["configurable"] -- always present, always correct."""
    user_id = test_case["user_id"]
    thread_id = test_case["thread_id"]
    return f"user={user_id} thread={thread_id}: {test_case['query']}"


def post_5243_agent(test_case: dict[str, Any]) -> str:
    """Node reads runtime.context -- missing for unmigrated callers."""
    rng = random.Random(hash(test_case["query"]) % 10_000)
    caller_migrated = rng.random() >= UNMIGRATED_CALLER_RATE
    user_id = test_case["user_id"] if caller_migrated else None
    thread_id = test_case["thread_id"] if caller_migrated else None
    return f"user={user_id} thread={thread_id}: {test_case['query']}"


def exact_match(output: str, test_case: dict[str, Any]) -> float:
    expected = (
        f"user={test_case['user_id']} thread={test_case['thread_id']}: "
        f"{test_case['query']}"
    )
    return 1.0 if output == expected else 0.0


def main() -> None:
    test_suite = [
        {"query": f"q_{i}", "user_id": f"user_{i}", "thread_id": f"thread_{i}"}
        for i in range(30)
    ]

    report = compare(
        version_a=pre_5243_agent,
        version_b=post_5243_agent,
        test_suite=test_suite,
        n_runs=50,
        metric="context_continuity_accuracy",
        scorer=exact_match,
    )
    print(report)

    # What a CI gate on the PR would have done, before merge:
    assert_no_regression(report)


if __name__ == "__main__":
    main()
