# agent-eval -- Lessons Log

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

## 2026-06-19 -- Mann-Whitney NaN for all-identical distributions

Pattern: scipy.stats.mannwhitneyu returns NaN p-value when all scores in both groups are identical.
Rule: Guard for np.isnan(p_value) immediately after mannwhitneyu call; return 1.0 (no significant difference). Do not propagate NaN.
Anti-sycophancy check: Discovered during test failures -- was not flagged proactively.

## 2026-06-19 -- Cohen's d zero-variance case requires sign

Pattern: When pooled std is 0.0 but means differ (constant-output agents with different constant values), cohens_d was returning 0.0, hiding a real effect.
Rule: When pooled_std == 0.0 and n_a > 1 and n_b > 1 and means differ, return np.copysign(np.inf, delta). Return 0.0 only for n=1 per group (undefined) or identical means.
Anti-sycophancy check: Discovered during test failures -- this enables REGRESSED/IMPROVED verdicts for constant-output agents, which is correct behavior.

## 2026-06-19 -- metric="accuracy" triggers exact_match_scorer

Pattern: compare() with metric="accuracy" and scorer=None silently applies exact_match_scorer. Any agent that returns a float (not str) will score 0.0 on every case, producing false STABLE verdicts on tests expecting float scores.
Rule: Float-returning agent tests must pass metric="performance" (or any non-"accuracy" string) when scorer is not provided. Document this in the scorer docstring.
Anti-sycophancy check: Caused 6 test failures -- discovered after the fact, not flagged proactively.

## 2026-06-19 -- Bootstrap CI test with constant arrays

Pattern: bootstrap_mean_ci([0.75]*50, [0.76]*50) always returns CI=[0.01, 0.01] because constant arrays have zero variance -- no bootstrap sampling variation. A test asserting ci.lower <= 0.0 <= ci.upper will always fail.
Rule: Tests for "CI contains zero for similar distributions" must use distributions with real variance (Gaussian samples), not constant arrays.
Anti-sycophancy check: Caught during test failures. The correct fix is Gaussian samples with seed=42, not widening CI bounds.

## 2026-06-19 -- docker-compose false claim

Pattern: docker-compose.yml was running python -m http.server 8080. README claimed this opened a regression dashboard at localhost:8080. It served a raw directory listing.
Rule: Never write README claims about functionality that doesn't exist in the code. If a UI isn't built, say "coming in v0.X", not "opens at localhost:8080 showing regression history".
Anti-sycophancy check: Caught in audit. Was written in the initial commit without verification.
