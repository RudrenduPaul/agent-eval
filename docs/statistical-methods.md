# Statistical Methods

This document explains the statistical tests used by agentregress and why each one was chosen over the alternatives. Written for ML engineers, not statisticians.

---

## The core question

Standard evals ask: "Does this agent response meet a quality bar?"

agentregress asks: "Are these two score distributions the same?"

These are different questions with different appropriate tests. Threshold-based evals use point estimates (is this score ≥ 0.7?). Distribution comparison requires inferential statistics.

---

## Mann-Whitney U test

### What it measures

Given two sets of scores S_A = {a_1, a_2, ..., a_m} and S_B = {b_1, b_2, ..., b_n}, the Mann-Whitney U statistic counts how often a score from B exceeds a score from A:

```
U = |{(i,j) : b_j > a_i}| + 0.5 × |{(i,j) : b_j = a_i}|
```

Under the null hypothesis that both distributions are identical, U converges to a known distribution. The p-value is the probability of observing this U (or more extreme) if the distributions were actually the same.

### Why not a t-test?

The t-test assumes both distributions are Gaussian with equal variance. LLM scores violate this assumption in practice:

- Scores are bounded to [0, 1], which truncates the tails
- Exact scores (0.0, 1.0) appear at high frequency -- discrete spikes in what should be continuous distributions
- Occasional API timeouts and failures create non-Gaussian outliers at 0.0

Mann-Whitney U makes no distributional assumptions. It is distribution-free. It is also robust to outliers: a single catastrophic failure at 0.0 shifts U by a predictable, bounded amount rather than pulling the mean to an extreme.

### Implementation

```python
from scipy import stats
result = stats.mannwhitneyu(arr_a, arr_b, alternative="two-sided", method="auto")
```

`method="auto"` selects exact computation for small n (< 25 per group) and asymptotic (normal approximation with tie correction) for larger n.

When all observations are identical across both groups, the test is degenerate and scipy returns NaN. agentregress handles this by returning p=1.0 (no significant difference detected, which is correct).

**Warning threshold:** n < 30 per group. At n=30, Mann-Whitney has approximately 80% power to detect a medium effect (Cohen's d = 0.5) at α=0.05. Below n=30, you may miss real regressions. agentregress warns but does not fail the gate on insufficient data.

---

## Bootstrap confidence intervals

### What it measures

The 95% CI on (mean_B - mean_A) answers: "Given the data I have, what is the plausible range of the true mean score delta?"

A CI of [-0.22, -0.07] means: "I'm 95% confident the true per-run accuracy drop is between 7 and 22 percentage points."

This is more actionable than a p-value alone. A p=0.001 result with CI=[-0.001, -0.0001] is statistically significant and operationally meaningless. A p=0.06 result with CI=[-0.30, -0.05] is worth investigating even if it doesn't cross the 0.05 threshold.

### Algorithm

1. Draw n_A samples with replacement from S_A → compute mean(resample_A)
2. Draw n_B samples with replacement from S_B → compute mean(resample_B)
3. delta_i = mean(resample_B) - mean(resample_A)
4. Repeat 1,000 times (default: `n_resamples=1000`)
5. CI = [percentile(deltas, 2.5), percentile(deltas, 97.5)]

### Why 1,000 resamples?

At 1,000 resamples, the Monte Carlo error in the CI boundary estimate is below 0.5 percentage points for typical agent score distributions. The compute cost is 26-31ms (measured). 10,000 resamples reduces MC error to 0.2 pp at 10x the cost -- not worth it for production CI.

### Reproducibility

Default seed=42. All comparisons with the same data and default parameters produce identical CIs across machines and Python versions. Pass `seed=None` to sample differently each run (not recommended for CI gates).

---

## Cohen's d (effect size)

### What it measures

Cohen's d separates statistical significance from operational significance:

```
d = (mean_B - mean_A) / s_p
```

where s_p is the pooled standard deviation:

```
s_p = sqrt(((n_A - 1) × var_A + (n_B - 1) × var_B) / (n_A + n_B - 2))
```

**Sign convention:** negative d = version B scored lower (regression). Positive d = version B scored higher (improvement).

**Interpretation:**

| |d| | Interpretation | In practice |
|---|---|---|
| < 0.2 | Negligible | Noise. Don't act. |
| 0.2 – 0.5 | Small | Investigate. Probably not user-facing. |
| 0.5 – 0.8 | Medium | Real. Likely user-facing on some tasks. |
| > 0.8 | Large | Critical. Act immediately. |

### The dual gate

agentregress fails the CI gate only when **both**:

- p < 0.05 (the shift is unlikely to be noise)
- |d| ≥ 0.2 (the shift is large enough to be operationally meaningful)

A shift at p=0.001 with d=0.04 is real but not worth blocking a deploy. A shift at p=0.06 with d=0.5 requires more data to confirm. The dual gate cuts false alarm rate substantially compared to p-value alone.

Both thresholds are configurable:

```python
report.assert_stable(
    p_threshold=0.01,  # stricter on evidence
    min_effect=0.5,    # only block on medium+ effects
)
```

### Zero-variance case

When all scores in both groups are identical (common in synthetic tests), the pooled std is 0. For n=1 per group, d is undefined and agentregress returns 0.0. For n>1 with equal within-group means but zero within-group variance, agentregress returns ±∞ (the groups are perfectly separated with no overlap -- the maximum possible effect).

---

## Rank-biserial r (non-parametric effect size)

The `compute_effect_sizes()` function also returns rank-biserial r, a non-parametric complement to Cohen's d:

```
r = 2U / (n_A × n_B) - 1
```

r ranges from -1 (B always loses) to +1 (B always wins). It is the effect size most directly interpretable alongside the Mann-Whitney U statistic.

---

## Minimum sample sizes

For the default gate (p < 0.05, d ≥ 0.2):

| Effect size | Required n per group for 80% power |
|---|---|
| Small (d=0.2) | ~200 |
| Medium (d=0.5) | ~34 |
| Large (d=0.8) | ~14 |

The default `n_runs=50` gives approximately 80% power for medium effects and 40-50% power for small effects. If catching small regressions matters, use n_runs=100-200 per version.

**Warning at n < 30:** Below 30 runs per group, Mann-Whitney has < 50% power to detect medium effects. The warning message explicitly states what sample size is needed.

**INSUFFICIENT_DATA at < 10 total scores:** Below 10 total scores per group, agentregress returns `Verdict.INSUFFICIENT_DATA` and `assert_stable()` does not raise, regardless of what the scores show. This prevents false positives from trivially small samples.

---

## Worked example

Version A (GPT-4o): 50 runs × 10 test cases = 500 scores, mean=0.840, std=0.060
Version B (GPT-4o-mini): 500 scores, mean=0.700, std=0.090

```
Mann-Whitney U:  p = 0.003
Bootstrap CI:    [-0.221, -0.067]  (95%)
Cohen's d:       -0.610  (medium-large regression)
```

Interpretation: The drop from 0.840 to 0.700 (delta=-0.140, or -16.7%) is statistically significant (p=0.003) and operationally large (medium effect). The CI tells you the true drop is between 6.7 and 22.1 percentage points with 95% confidence. `assert_stable()` raises `AssertionError`.

---

## References

- Mann, H.B., & Whitney, D.R. (1947). On a test of whether one of two random variables is stochastically larger than the other. *Annals of Mathematical Statistics*, 18(1), 50-60.
- Cohen, J. (1988). *Statistical power analysis for the behavioral sciences* (2nd ed.). Hillsdale, NJ: Lawrence Erlbaum Associates.
- Efron, B., & Tibshirani, R.J. (1993). *An Introduction to the Bootstrap*. Chapman & Hall.
- scipy.stats.mannwhitneyu: https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.mannwhitneyu.html
