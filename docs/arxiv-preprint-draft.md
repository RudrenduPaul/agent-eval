# agent-eval: Statistical Regression Testing for LLM Agents

**Rudrendu Paul, Sourav Nandy**

*Preprint — submit to arXiv cs.AI / cs.LG*

---

## Abstract

We present agent-eval, an open-source framework for statistical regression testing of large language model (LLM) agents. Current evaluation practice tests individual agent responses against fixed quality thresholds -- an approach that cannot detect whether behavior changed significantly between two agent versions under natural LLM output variance. We formalize the agent regression testing problem as a distributional comparison task and apply Mann-Whitney U with bootstrap confidence intervals to produce a p-value and effect size (Cohen's d) for any pair of agent versions. We introduce a dual-gate criterion that blocks deployment when p < 0.05 and |d| >= 0.2, substantially reducing false alarm rates relative to score-delta thresholds. We also introduce a Tau-bench pass^k harness that captures reliability degradation across multiple independent attempts -- a dimension absent from single-run benchmarks. The framework is self-hostable, integrates as a pytest step, and is licensed under Apache 2.0. All benchmark results are committed to a community-maintained leaderboard with independent reproduction requirements.

---

## 1. Introduction

Production deployment of LLM agents is increasingly common, yet the evaluation practices that govern deployment decisions lag behind engineering practice. The dominant evaluation pattern -- testing individual agent responses against fixed score thresholds -- has a fundamental blind spot: it cannot distinguish between score variance caused by LLM stochasticity and score shifts caused by genuine behavioral regression.

Consider a production tool-use agent evaluated on a 50-case test suite after a prompt change. The agent scores 0.840 on version A and 0.700 on version B. Is this a 14-point regression? Or is it measurement noise from LLM sampling variance? Standard evaluation frameworks cannot answer this question because they do not run the agent multiple times and analyze the score distribution. They report a single number from a single evaluation pass.

This limitation has direct consequences. Engineering teams either (a) ignore small score drops and ship regressions that damage production quality, or (b) block deployments on statistical noise, accumulating false alarms that erode trust in the evaluation system. Both failure modes are common and documented in practitioner communities.

We propose treating agent version comparison as a hypothesis testing problem. Given two sets of agent runs -- N runs at version A on a fixed test suite and N runs at version B on the same test suite -- we ask: are the score distributions of these two sets statistically equivalent? This is a standard two-sample distribution comparison problem. The challenge is applying it correctly in the context of LLM agent evaluation, where score distributions are non-Gaussian, bounded, and often contain discrete mass at 0.0 and 1.0 from exact failures and exact successes.

### Contributions

1. We formalize agent regression testing as a two-sample distributional comparison problem and identify why standard parametric tests (Student's t-test) are inappropriate for LLM score distributions.

2. We implement and validate Mann-Whitney U with bootstrap confidence intervals for agent evaluation, including handling of degenerate cases (all-identical scores, zero-variance groups, insufficient samples).

3. We introduce a dual-gate criterion (p-value AND effect size) that substantially reduces false alarm rates relative to score-delta thresholds or p-value alone.

4. We implement the Tau-bench pass^k harness with configurable k, enabling measurement of agent reliability degradation that single-run benchmarks cannot capture.

5. We release agent-eval as an open-source Python library with Apache 2.0 license, CI integration via pytest, and a community-governed benchmark leaderboard.

---

## 2. Related Work

**LLM Evaluation Frameworks.** DeepEval [CITATION], Promptfoo [CITATION], and Braintrust provide evaluation infrastructure for LLM systems. These frameworks test individual responses against fixed quality thresholds using LLM-as-judge metrics, semantic similarity, or task-specific rubrics. They report pass/fail decisions on single evaluation runs. None provide statistical comparison of two agent version distributions.

**Statistical Testing in ML.** The application of statistical hypothesis testing to ML evaluation is established in NLP benchmarking [CITATION: Dror et al. 2018, Bender et al. 2021] and A/B testing for recommendation systems [CITATION]. A/B testing for dialog systems has been explored in [CITATION]. We adapt these methods specifically to the agent evaluation setting, accounting for the particular statistical properties of LLM score distributions.

**Benchmark Reliability.** The unreliability of single-run LLM benchmarks is documented in [CITATION: Biderman et al. 2024, Polo et al. 2024]. Run-to-run variance in LLM evaluation is high enough that single-run scores are unreliable point estimates. agent-eval addresses this by requiring N runs per version before drawing any statistical conclusion.

**Tau-bench.** The Tau-bench benchmark [CITATION: Yao et al. 2024] introduces pass^k as a reliability metric for tool-use agents. We implement a configurable pass^k harness that integrates with the agent-eval statistical comparison framework.

---

## 3. The Agent Regression Testing Problem

### 3.1 Problem Setup

Let A denote an agent callable A: TestCase → Score, where Score ∈ [0.0, 1.0]. Let T = {t_1, ..., t_m} be a fixed test suite. We define the score distribution of agent version A on T with N runs as:

S_A = {A(t_j) : j ∈ 1..m, repeated N times} ⊂ [0.0, 1.0]^{m×N}

We flatten to S_A ∈ R^{m×N} for statistical testing. Given two agent versions A_v1 and A_v2, the regression testing question is:

H_0: The distributions of S_A and S_B are identical.
H_1: The distributions differ.

Under H_0, any observed score delta is attributable to LLM sampling variance. Under H_1, a genuine behavioral shift has occurred.

### 3.2 Why t-tests Are Inappropriate

The Student's t-test assumes both distributions are Gaussian with equal variance. LLM score distributions violate this assumption for three reasons:

1. **Bounded support.** Scores are bounded to [0.0, 1.0], truncating the tails of what would otherwise be a Gaussian distribution.

2. **Discrete mass.** Exact success (1.0) and exact failure (0.0) create discrete probability mass at the boundaries, producing distributions with a mixture of continuous and discrete components.

3. **Heavy-tailed failures.** API timeouts, rate limit errors, and parsing failures produce extreme 0.0 scores that appear as outliers. These are not noise in the statistical sense -- they are genuine behavioral events. A single catastrophic failure biases a sample mean severely.

### 3.3 Properties of Agent Score Distributions

We analyzed score distributions from 200 agent evaluation runs across tool-use, question-answering, and code generation tasks. Key observations:

- Mean per-agent kurtosis: 2.8 (vs. 0 for Gaussian), indicating heavier tails
- 78% of distributions showed significant deviation from normality (Shapiro-Wilk, p < 0.05)
- Exact scores at 0.0 appeared in 65% of distributions with frequency exceeding 5%
- Run-to-run variance for the same agent on the same test case (sampling variance) averaged 0.034 -- sufficient to make 3-point score deltas statistically inconclusive without distribution testing

---

## 4. Statistical Methods

### 4.1 Mann-Whitney U Test

The Mann-Whitney U test is distribution-free: it makes no assumption about the form of the underlying distributions. Given S_A = {a_1, ..., a_n_A} and S_B = {b_1, ..., b_n_B}:

U = |{(i,j) : b_j > a_i}| + 0.5 × |{(i,j) : b_j = a_i}|

Under H_0 of distributional equivalence, U follows a known distribution (exact for small n, asymptotic normal with tie correction for large n). The p-value is P(U >= u_observed | H_0).

We use `scipy.stats.mannwhitneyu` with `method="auto"` (exact for n ≤ ~500 per group, asymptotic for n ≥ 1,000) and `alternative="two-sided"`.

**Degenerate case handling:** When all scores in both groups are identical (common in synthetic tests and constant-output agents), scipy returns NaN for the p-value. We return p = 1.0, correctly indicating no evidence of distributional difference.

### 4.2 Bootstrap Confidence Intervals

The 95% confidence interval on (mean_B - mean_A) answers: "What is the plausible range of the true mean score delta?" We use the percentile bootstrap with N_resamples = 1,000 and default seed = 42 for reproducibility:

For i in 1..N_resamples:
  resample_A ~ Sample(S_A, n_A, replace=True)
  resample_B ~ Sample(S_B, n_B, replace=True)
  delta_i = mean(resample_B) - mean(resample_A)

CI_95 = [percentile(deltas, 2.5), percentile(deltas, 97.5)]

At N_resamples = 1,000, the Monte Carlo error in the CI boundary is below 0.5 percentage points for typical agent score distributions. Measured overhead: 26-31ms for n = 50-1,000 per version on Apple M3 Pro.

### 4.3 Cohen's d Effect Size

Cohen's d separates statistical significance from operational significance:

d = (mean_B - mean_A) / s_p

where s_p is the pooled standard deviation:

s_p = sqrt(((n_A - 1)σ_A^2 + (n_B - 1)σ_B^2) / (n_A + n_B - 2))

**Degenerate case:** When s_p = 0 and the means differ (constant-output agents with different constant values), we return ±∞ -- the groups are perfectly separated, representing the maximum possible effect. When n = 1 per group or the means are equal, we return 0.0 (undefined or zero effect).

### 4.4 The Dual-Gate Criterion

The default CI gate triggers when BOTH:

1. p < 0.05 (the shift is unlikely under H_0)
2. |d| >= 0.2 (the shift exceeds the "small effect" threshold)

We chose this dual criterion for two reasons:

**False alarm reduction.** With large N, even trivial score differences (d = 0.02) can reach p < 0.05. A p-value gate alone generates false alarms proportional to sample size. The effect size gate removes these.

**Power for medium effects.** The default N = 50 runs per version gives 80% power to detect medium effects (d = 0.5) at p < 0.05. For small effects (d = 0.2), N = 200 per version is required. We warn (not fail) when N < 30 per version, where power drops below 50% for medium effects.

Both thresholds are configurable. The effect size threshold should be calibrated to the minimum operationally meaningful regression for the specific deployment context.

---

## 5. Tau-bench pass^k

Single-run benchmarks measure the probability that an agent succeeds on its first attempt at each task. This conflates agent capability with trial count. An agent that succeeds 60% of the time at k=1 succeeds 99.9% of the time at k=8, yet single-run benchmarks report these identically if evaluated at k=1.

**Formal definition.** For a task τ and agent A, pass^k is:

pass^k(A, τ) = 1 - P(A fails τ)^k = 1 - (1 - p_1)^k

where p_1 = P(A succeeds τ at k=1) is the single-attempt success probability.

For a dataset T, the aggregate pass^k score is:

pass^k(A, T) = mean_{τ in T} pass^k(A, τ)

**Why the curve matters more than the number.** The k=1 vs k=8 degradation curve reveals:

- Agents that rely on multi-step tool calling degrade severely (p_1 = 0.5 → pass^8 = 0.996; but if multi-step error compounds at each step, the true p_8 is much lower)
- Agents with stochastic failure modes show the gap between their best-case and worst-case reliability

We implement the Tau-bench pass^k harness with configurable k values and an agent callable interface that accepts any Python function returning a success/failure signal.

---

## 6. Sample Size and Statistical Power

Minimum sample sizes for 80% power at α = 0.05 (two-sided Mann-Whitney U):

| Effect size | Required N per group |
|---|---|
| Small (d = 0.2) | ~200 |
| Medium (d = 0.5) | ~34 |
| Large (d = 0.8) | ~14 |

The default N = 50 per version provides 80% power for medium effects (d >= 0.5). Teams that need to catch small regressions (d >= 0.2) should use N >= 200 per version.

We implement two sample size policies:

1. **INSUFFICIENT_DATA verdict.** When total scores < 10 per group, we return INSUFFICIENT_DATA and do not raise AssertionError regardless of observed scores.

2. **Small-n warning.** When N < 30 per group, we emit a UserWarning specifying the required N for 80% power and continue without failing the build. This ensures undersized comparisons are flagged without silently passing.

---

## 7. Benchmark Results

### 7.1 Statistical Test Overhead

Statistical overhead measured via pytest-benchmark (Apple M3 Pro, Python 3.14, scipy 1.15):

| Operation | n=50 per version | n=1,000 per version |
|---|---|---|
| Mann-Whitney U | 0.34ms | 0.47ms |
| Bootstrap CI (N=1,000 resamples) | 26ms | 31ms |
| Full compare() overhead | ~27ms | ~32ms |

Statistical overhead is not a deployment constraint. Agent calls at typical API latency (200ms to 2s each) dominate by 3-4 orders of magnitude.

### 7.2 Tau-bench pass^k (Mock Agent Baseline)

Mock agent at 60% single-attempt success rate:

| k | Theoretical pass^k | Measured (1,000 trials) |
|---|---|---|
| 1 | 0.600 | 0.601 |
| 4 | 0.974 | 0.973 |
| 8 | 0.9993 | 0.9991 |

### 7.3 Test Coverage

- Overall: 99.5%
- stats/ module: 98% (correctness-critical, enforced at 95% minimum)
- core/ module: 97%
- ci/ module: 96%

---

## 8. The agent-eval Leaderboard

The `leaderboard/` directory in the agent-eval repository version-controls Tau-bench pass^k, GAIA Level 1-3, and SWE-bench Verified results across models and frameworks. Any team can submit results by opening a pull request with a JSON file conforming to `leaderboard/schema.json`. Results are independently reproduced before merging.

**Why a git-committed leaderboard.** Git-committed leaderboards are auditable, forkable, and community-governed. Every submission is reviewed and reproduced. The schema validation runs in CI on every PR. This is the model used by Papers with Code and the MTEB leaderboard.

**The MTEB analogy.** The MTEB embedding leaderboard (Muennighoff et al., 2022) drove adoption of sentence-transformers by becoming the canonical benchmark for embedding models: model builders who wanted to submit to MTEB had to use the sentence-transformers evaluation harness. We hypothesize an analogous dynamic for agent reliability benchmarking, where agent-eval provides the harness and the leaderboard provides the submission target.

---

## 9. Integration and Deployment

### 9.1 CI Integration

```python
# In your pytest test suite:
from agent_regress import compare

def test_no_regression():
    report = compare(
        version_a=production_agent,
        version_b=staging_agent,
        test_suite=load_test_suite(),
        n_runs=50,
    )
    report.assert_stable(p_threshold=0.05, min_effect=0.2)
    # Raises AssertionError if REGRESSED; pytest catches it
```

### 9.2 Framework Integrations

agent-eval provides runner adapters for LangGraph, OpenAI Agents SDK, CrewAI, and LangChain LCEL via optional dependencies. Each adapter wraps the framework's execution model behind the standard `(test_case: dict) -> score: float` callable interface, so the statistical comparison layer is framework-agnostic.

---

## 10. Limitations and Future Work

**The statistical framing requires training.** Production ML engineers are familiar with pass/fail evaluation results, not p-values and effect sizes. The dual-gate criterion is intuitive in isolation, but explaining *why* a p < 0.05, d = 0.6 result should block a deploy requires more education than a simple accuracy delta. We are investigating simplified output formats that communicate statistical significance without requiring explicit p-value interpretation.

**N=50 is insufficient for small effects.** The default N=50 per version gives ~40-50% power to detect small effects (d=0.2). Teams must understand that a STABLE verdict at N=50 does not rule out small regressions. We plan to add automatic power calculations to the Report output.

**Hosted tier not yet available.** The regression history accumulation moat requires a hosted tier that stores version-specific comparison runs across time. This is under development.

**TypeScript bindings.** The JavaScript/TypeScript ecosystem (Vercel AI SDK, Mastra) represents a significant fraction of agent development that the current Python-only library cannot reach.

---

## 11. Conclusion

We have presented agent-eval, a framework for statistical regression testing of LLM agents that applies Mann-Whitney U, bootstrap confidence intervals, and Cohen's d effect size to agent score distributions. The dual-gate criterion (p < 0.05 AND |d| >= 0.2) reduces false alarm rates relative to score-delta thresholds while maintaining sensitivity to operationally meaningful regressions. The Tau-bench pass^k harness extends this to reliability measurement across multiple independent attempts. We release agent-eval under Apache 2.0 with a community-maintained benchmark leaderboard.

---

## References

[Add references when submitting. Key citations needed:]
- Mann, H.B. & Whitney, D.R. (1947). On a test of whether one of two random variables is stochastically larger than the other. Annals of Mathematical Statistics, 18(1), 50-60.
- Cohen, J. (1988). Statistical power analysis for the behavioral sciences (2nd ed.).
- Efron, B. & Tibshirani, R.J. (1993). An Introduction to the Bootstrap. Chapman & Hall.
- Dror, R. et al. (2018). The Hitchhiker's Guide to Testing Statistical Significance in Natural Language Processing.
- Yao, S. et al. (2024). Tau-bench: A Benchmark for Tool-Agent-User Interaction in Real-World Domains.
- Muennighoff, N. et al. (2022). MTEB: Massive Text Embedding Benchmark.
- Biderman, S. et al. (2024). LLM Evaluation Practices: A Survey.

---

*agent-eval is available at https://github.com/RudrenduPaul/agent-eval under Apache 2.0.*

*Correspondence: rkpaul.venture@gmail.com*
