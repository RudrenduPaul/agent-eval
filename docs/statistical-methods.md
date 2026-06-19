# Statistical Methods

## Mann-Whitney U Test

Given two sets of scores S_A and S_B, the Mann-Whitney U statistic counts pairs (a, b)
where b greater than a.

Under H0 (distributions identical), U is asymptotically normal. The p-value is computed
via scipy.stats.mannwhitneyu with method="auto" (exact for small n, normal approximation
for larger n).

Why not a paired t-test: Agent scores are not normally distributed. The U test is
distribution-free and appropriate.

## Bootstrap Confidence Interval

To construct a 95% CI on (mean_B - mean_A):

1. Draw n_A samples with replacement from S_A
2. Draw n_B samples with replacement from S_B
3. Compute delta = mean(S_B sample) - mean(S_A sample)
4. Repeat 1000 times
5. CI = [percentile(deltas, 2.5), percentile(deltas, 97.5)]

Default: 1000 resamples, 95% confidence, seed=42 for reproducibility.

## Cohen's d (pooled standard deviation)

d = (mean_B - mean_A) / s_p

where s_p is the pooled standard deviation.

Sign convention: negative d means version B scored lower (regression).
Positive d means version B scored higher (improvement).

## Minimum Sample Size

For 80% power to detect a small effect (d=0.2) at alpha=0.05, the required
sample size per group is approximately 200. For a medium effect (d=0.5),
approximately 34 per group.

agentregress defaults to n=50 per version, which gives roughly 85% power
for medium effects and warns at n less than 30.
