# agentregress -- Lessons Log

Read this file at the start of every session before writing code.

---

## 2026-06-19 -- Initial repo setup

Pattern: stats/ module must stay pure Python + scipy. Any LLM import in stats/ breaks the isolation invariant.
Rule: grep for "import openai" and "import langchain" in stats/ before every commit.
Anti-sycophancy check: Flagged proactively during architecture design.

## 2026-06-19 -- Sample size threshold

Pattern: reporting a p-value with n < 10 per group is statistically meaningless.
Rule: raise ValueError if n < 10 total; warn (not fail) if n < 30 per group.
Anti-sycophancy check: Added proactively.

## 2026-06-19 -- Gate behavior on insufficient data

Pattern: CI gate should WARN, not fail, when sample size is too small.
Rule: assert_no_regression() returns without raising when n_a < 30 or n_b < 30. Always warn.
Anti-sycophancy check: Flagged in [redacted] invariants section.
