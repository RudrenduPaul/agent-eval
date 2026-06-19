# agentregress

Find out if your latest agent deploy made things worse -- statistically.

[![PyPI](https://img.shields.io/pypi/v/agent-regress)](https://pypi.org/project/agent-regress/)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![CI](https://github.com/RudrenduPaul/agentregress/actions/workflows/ci.yml/badge.svg)](https://github.com/RudrenduPaul/agentregress/actions/workflows/ci.yml)
[![OpenSSF Scorecard](https://api.securityscorecards.dev/projects/github.com/RudrenduPaul/agentregress/badge)](https://api.securityscorecards.dev/projects/github.com/RudrenduPaul/agentregress)

## Install

```bash
pip install agent-regress
# or
uv add agent-regress
```

## What this does

You changed a prompt. Or switched from GPT-4o to GPT-4o-mini to cut costs. Or a dependency
updated silently. Your evals still pass -- because they check individual responses against
fixed thresholds, not whether behavior shifted across the whole distribution.

agentregress runs your agent 50 times on a fixed test suite at version A, then 50 times at
version B, and asks: are these two score distributions the same? It uses Mann-Whitney U and
bootstrap confidence intervals to give you a p-value and effect size. If behavior shifted
significantly, the CI build fails with a clear message:

```
REGRESSED: tool_accuracy dropped 14.2% (p=0.003, Cohen's d=-0.61, 95% CI [-0.22, -0.07])
Version A: 0.840 +/- 0.060  (n=50)
Version B: 0.700 +/- 0.090  (n=50)
```

If it did not shift, you get a green gate:

```
STABLE: no statistically significant behavior change detected (p=0.41, n=50 per version)
```

This is A/B testing for agent quality. Nothing in DeepEval, Promptfoo, or Braintrust
answers this question directly.

## First comparison

```python
from agent_regress import compare

# Your agent as a Python callable: takes a test case dict, returns a float score 0.0-1.0
def my_agent_v1(test_case: dict) -> float:
    # your existing agent code
    ...

def my_agent_v2(test_case: dict) -> float:
    # your updated agent code
    ...

# Your test suite: a list of dicts
test_suite = [
    {"query": "find the product SKU for order 8823", "expected": "SKU-4492"},
    # ... more test cases
]

report = compare(
    version_a=my_agent_v1,
    version_b=my_agent_v2,
    test_suite=test_suite,
    n_runs=50,          # runs per version per test case
    metric="accuracy",  # or pass a custom scorer function
)

print(report)          # p-value, effect size, CI, verdict
report.assert_stable() # raises AssertionError if REGRESSED -- caught by pytest
```

## CI gate -- fail the build on regression

```python
# test_regression.py
from agent_regress import compare

def test_no_regression():
    report = compare(
        version_a=agent_v1,
        version_b=agent_v2,
        test_suite=load_test_suite(),
        n_runs=50,
    )
    report.assert_stable(p_threshold=0.05, min_effect=0.2)
    # raises AssertionError if behavior regressed -- pytest catches it
```

```bash
uv run pytest test_regression.py
```

Add this to CI. It catches regressions that pass your unit evals.

## Custom scorer

Agent returns text? Pass a scorer to convert it to a float:

```python
def my_scorer(output: str, test_case: dict) -> float:
    return 1.0 if output.strip() == test_case["expected"] else 0.0

report = compare(
    version_a=agent_v1,
    version_b=agent_v2,
    test_suite=test_suite,
    n_runs=50,
    scorer=my_scorer,
)
```

## Why p-values and not just score deltas

A 3-point drop in accuracy might be noise from run-to-run LLM variance. Or it might be a
real regression. Without statistical testing you cannot tell which -- so teams either ignore
small drops (and miss real problems) or escalate everything (and drown in false alarms).

p-values let you set a threshold in advance (we act on changes at p < 0.05) and stick to it.
Cohen's d tells you whether the effect is large enough to matter regardless of statistical
significance (a p=0.001 change with d=0.04 is statistically significant and operationally
meaningless). Together they cut false alarm rate and catch real regressions your eval suite
cannot see.

**Sample size:** agentregress warns if you run fewer than 30 trials per version. It does not
fail the build on insufficient data -- it tells you the sample is too small to trust the result.

## Benchmarks

Statistical test overhead -- the time to run the comparison itself (not the agent calls):

| Operation | n=50 per version | n=1000 per version |
|---|---|---|
| Mann-Whitney U | less than 1ms | less than 5ms |
| Bootstrap CI (1000 resamples) | less than 10ms | less than 50ms |
| Full compare() statistical overhead | less than 15ms | less than 60ms |

The agent calls are the bottleneck. The statistics are not.

To reproduce:

```bash
git clone https://github.com/RudrenduPaul/agentregress
cd agentregress
uv sync --extra dev
uv run pytest benchmarks/test_stat_overhead.py --benchmark-only -v
```

## How agentregress differs from the alternatives

| Feature | agentregress | DeepEval | Braintrust | Promptfoo |
|---|---|---|---|---|
| Statistical version comparison (p-values) | Yes | No | No | No |
| Effect size reporting (Cohen's d) | Yes | No | No | No |
| Bootstrap confidence intervals (95% CI) | Yes | No | No | No |
| Self-hostable CI gate (zero SaaS) | Yes | Partial | No | Yes |
| Tau-bench pass^k harness (k=1,4,8) | Yes | No | No | No |
| Sample size warnings below n=30 | Yes | No | No | No |
| Core license | Apache 2.0 | MIT | SaaS only | MIT* |
| Requires cloud account | No | Optional | Yes | No |

*Promptfoo is now owned by OpenAI (acquired March 2026).

**The key difference from DeepEval:** DeepEval tests whether an individual response meets a
quality threshold (pass/fail against a fixed standard). agentregress tests whether behavior
changed significantly between two version distributions. Different statistical question,
different tool.

## Integration matrix

| Framework | Status | Install |
|---|---|---|
| LangGraph | Shipped (v0.1) | `pip install agent-regress[langgraph]` |
| OpenAI Agents SDK | Shipped (v0.1) | `pip install agent-regress[openai-agents]` |
| CrewAI | Shipped (v0.1) | `pip install agent-regress[crewai]` |
| LangChain LCEL | Shipped (v0.1) | `pip install agent-regress[langchain]` |
| AutoGen | Planned (v0.3) | |
| Vercel AI SDK (TypeScript) | Planned (v0.4) | |

## Self-host

```bash
git clone https://github.com/RudrenduPaul/agentregress
cd agentregress
docker compose up -d
```

Opens at `http://localhost:8080`. No account, no API key, no telemetry sent anywhere.

## Stability badge

Add to your agent repo README after setting up agentregress in CI:

```markdown
[![agentregress](https://img.shields.io/badge/agentregress-stable-brightgreen)](https://github.com/RudrenduPaul/agentregress)
```

## Leaderboard

The `leaderboard/` directory tracks Tau-bench pass^k, GAIA, and SWE-bench results across
models and frameworks. Submit results by opening a PR with a JSON file matching
`leaderboard/schema.json`. Results are reproduced independently before merging.

See [leaderboard/README.md](leaderboard/README.md) for the methodology and submission process.

## Community

- Discord: discord.gg/agentregress (#general, #stat-methods, #leaderboard, #contributing)
- GitHub Discussions: design questions before writing code
- Contributing: [CONTRIBUTING.md](CONTRIBUTING.md) -- good first issues labeled in GitHub

Apache 2.0. Contributions welcome.

---

*Built by Rudrendu Paul and Sourav Nandy*
