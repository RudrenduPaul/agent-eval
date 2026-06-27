# Core Concepts

## What "statistical regression" means here

agent-eval detects a statistically significant shift in agent behavior distribution
between two versions.

**It DOES mean:**
- A statistically significant change in the score distribution from version A to version B
- p-value less than 0.05 combined with Cohen's d greater than 0.2 (or your configured thresholds)
- A reliable detection that behavior changed

**It DOES NOT mean:**
- Every individual run in version B is worse
- The agent is broken or unusable (REGRESSED is a statistical finding, not a severity judgment)
- Explaining why behavior changed (agent-eval detects; your team diagnoses)

## Mann-Whitney U test

agent-eval uses Mann-Whitney U rather than a t-test because:

1. Agent scores are often not normally distributed
2. The U test makes no distributional assumptions
3. It is robust to outliers from occasional API failures

## Cohen's d effect size

p less than 0.05 tells you the shift is unlikely to be noise. Cohen's d tells you whether
the shift is large enough to care about. A p=0.001 result with d=0.04 is statistically
significant and operationally meaningless.

Conventions:
- d less than 0.2: negligible
- 0.2 to 0.5: small
- 0.5 to 0.8: medium
- d greater than 0.8: large

The default CI gate fails only when p less than 0.05 AND d is 0.2 or greater.

## Bootstrap confidence intervals

The 95% CI shows the likely range of the true mean score delta. If the CI is [-0.22, -0.07],
you can be 95% confident the true per-run score drop is between 7 and 22 percentage points.

agent-eval uses 1000 bootstrap resamples by default, seeded at 42 for reproducibility.

## Tau-bench pass^k

pass^k measures the probability that an agent succeeds on at least one attempt out of k runs.
The k=1 vs k=8 curve is the signal that matters -- single-run benchmarks miss degradation.
