# agentregress

**Statistical regression testing for LLM agents.** Run your agent 50 times on a fixed test suite at version A, 50 times at version B, and get a p-value on whether behavior actually changed -- not just whether the score looks different.

[![PyPI](https://img.shields.io/pypi/v/agent-regress)](https://pypi.org/project/agent-regress/)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![CI](https://github.com/RudrenduPaul/agentregress/actions/workflows/ci.yml/badge.svg)](https://github.com/RudrenduPaul/agentregress/actions/workflows/ci.yml)
[![Coverage: 99%](https://img.shields.io/badge/coverage-99%25-brightgreen)](https://github.com/RudrenduPaul/agentregress/actions)
[![OpenSSF Scorecard](https://api.securityscorecards.dev/projects/github.com/RudrenduPaul/agentregress/badge)](https://api.securityscorecards.dev/projects/github.com/RudrenduPaul/agentregress)

---

## Install

```bash
pip install agent-regress
# or
uv add agent-regress
```

## The problem this solves

You changed a prompt. Or switched from GPT-4o to GPT-4o-mini to cut costs. Or a dependency updated silently. Your evals still pass -- because they test individual responses against fixed thresholds. They don't detect whether behavior shifted across the whole distribution.

A 3-point drop in accuracy might be noise from LLM variance. Or it might be a real regression. Without statistical testing you cannot tell which. Teams either ignore small drops and miss real problems, or escalate everything and drown in false alarms.

agentregress answers the distributional question with a p-value and effect size:

```
============================================================
agentregress Report -- tool_accuracy
============================================================
Verdict:    REGRESSED
p-value:    0.0031
Cohen's d:  -0.610
95% CI:     [-0.221, -0.067]

Version A:  0.8400 +/- 0.0601  (n=50)
Version B:  0.7000 +/- 0.0903  (n=50)
Delta:      -0.1400
============================================================
```

When CI fails, the assertion error gives the deploy-blocking message:

```
AssertionError: REGRESSED: tool_accuracy dropped 16.7%
(p=0.003, Cohen's d=-0.61, 95% CI [-0.22, -0.07])
Version A: 0.840 +/- 0.060  (n=50)
Version B: 0.700 +/- 0.090  (n=50)
```

When nothing changed:

```
Verdict:    STABLE
p-value:    0.4100
Cohen's d:  0.021
```

This is A/B testing for agent quality. DeepEval, Promptfoo, and Braintrust test whether individual responses meet thresholds. None of them answer: *did this version's behavior distribution shift significantly from the last?*

---

## Quickstart

```python
from agent_regress import compare

# Any callable that takes a test case dict and returns a score 0.0-1.0
def agent_v1(test_case: dict) -> float:
    ...  # your existing agent

def agent_v2(test_case: dict) -> float:
    ...  # your updated agent

test_suite = [
    {"query": "find SKU for order 8823", "expected": "SKU-4492"},
    # ... more test cases
]

report = compare(
    version_a=agent_v1,
    version_b=agent_v2,
    test_suite=test_suite,
    n_runs=50,
)

print(report)           # structured output with p-value, CI, effect size
report.assert_stable()  # raises AssertionError if behavior regressed
```

Agent returns text? Pass a scorer:

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

---

## Add to CI: fail the build on regression

```python
# test_regression.py -- add to your existing test suite
from agent_regress import compare

def test_no_regression():
    report = compare(
        version_a=production_agent,
        version_b=staging_agent,
        test_suite=load_test_suite(),
        n_runs=50,
    )
    report.assert_stable(
        p_threshold=0.05,  # act on changes at p < 0.05
        min_effect=0.2,    # Cohen's d threshold -- ignore noise below 0.2
    )
```

```bash
uv run pytest test_regression.py
```

Add the stability badge to your agent repo:

```markdown
[![agentregress](https://img.shields.io/badge/agentregress-stable-brightgreen)](https://github.com/RudrenduPaul/agentregress)
```

---

## How it differs from the alternatives

| Capability | agentregress | DeepEval | Braintrust | Promptfoo |
|---|---|---|---|---|
| Statistical version comparison (p-values) | **Yes** | No | No | No |
| Effect size reporting (Cohen's d) | **Yes** | No | No | No |
| Bootstrap 95% confidence intervals | **Yes** | No | No | No |
| Distributional shift detection | **Yes** | No | No | No |
| Tau-bench pass^k harness (k=1,4,8) | **Yes** | No | No | No |
| GAIA Level 1-3 split harness | **Yes** | No | No | No |
| SWE-bench scaffold score harness | **Yes** | No | No | No |
| Self-hostable, zero SaaS required | **Yes** | Partial | No | Yes |
| Sample size warnings (n < 30) | **Yes** | No | No | No |
| Core license | Apache 2.0 | MIT | Proprietary | MIT† |
| Requires cloud account | No | Optional | Yes | No |
| Test type | Distributional | Threshold | Threshold | Threshold |

†Promptfoo acquired by OpenAI, March 2026.

**The one-sentence distinction from DeepEval:** DeepEval tests whether an individual agent response clears a quality bar. agentregress tests whether behavior changed significantly between two agent versions -- a different statistical question that threshold testing cannot answer.

**[redacted]** The scipy Mann-Whitney U call is one line. Any SaaS eval platform can add it.

**[redacted]** The version-specific regression history accumulated over months of production use, and a community-maintained benchmark leaderboard with independent result verification. [redacted]

---

## Statistical methods

agentregress uses three statistical tests, applied in combination:

**Mann-Whitney U** compares two score distributions without assuming normality. LLM scores are not Gaussian -- the U test is distribution-free and robust to the long tails and bimodal distributions that appear in real agent outputs.

**Bootstrap confidence intervals** (1,000 resamples, seed=42) give a 95% CI on the mean score delta. The CI tells you *how large* the shift was: a CI of [-0.22, -0.07] means you can be 95% confident the true per-run accuracy drop is between 7 and 22 percentage points.

**Cohen's d** (pooled standard deviation) separates statistical significance from operational significance. A shift at p=0.001 with d=0.04 is real but meaningless. A shift at p=0.06 with d=0.5 is operationally large but requires more data to confirm. The default CI gate acts only when *both* p < 0.05 and d ≥ 0.2.

See [docs/statistical-methods.md](docs/statistical-methods.md) for the full methodology.

---

## Benchmarks

Statistical test overhead -- time to run the comparison itself, not the agent calls. **Agent calls are the bottleneck. The statistics are not.**

Measured on Apple M3 Pro, Python 3.14, scipy 1.15, numpy 2.2:

| Operation | n=50 per version | n=1,000 per version |
|---|---|---|
| Mann-Whitney U | **0.34ms** | **0.47ms** |
| Bootstrap CI (1,000 resamples) | **26ms** | **31ms** |
| Full compare() statistical overhead | **~27ms** | **~32ms** |

Reproduce:

```bash
git clone https://github.com/RudrenduPaul/agentregress
cd agentregress
uv sync --extra dev
uv run pytest benchmarks/test_stat_overhead.py --benchmark-only -v
```

---

## Integration matrix

| Framework | Status | Install |
|---|---|---|
| LangGraph | Shipped (v0.1) | `pip install agent-regress[langgraph]` |
| OpenAI Agents SDK | Shipped (v0.1) | `pip install agent-regress[openai-agents]` |
| CrewAI | Shipped (v0.1) | `pip install agent-regress[crewai]` |
| LangChain LCEL | Shipped (v0.1) | `pip install agent-regress[langchain]` |
| AutoGen | Planned (v0.3) | |
| Vercel AI SDK (TypeScript) | Planned (v0.4) | |

---

## Standard benchmarks

agentregress ships harnesses for the three standard agent benchmarks:

**Tau-bench pass^k** measures reliability across k independent attempts. Single-run benchmarks miss degradation -- an agent that succeeds 65% of the time at k=1 reaches 97% at k=8. The k=1 vs k=8 curve is the signal.

```python
from agent_regress.benchmarks.tau_bench import TauBenchHarness

harness = TauBenchHarness(agent=my_agent, dataset=tau_bench_dataset)
results = harness.evaluate(k_values=[1, 4, 8])
```

**GAIA Level 1-3 split** stratifies by task difficulty. Overall accuracy hides per-difficulty regressions -- a prompt change that helps Level 1 often hurts Level 3.

**SWE-bench scaffold score** isolates framework contribution from model contribution.

See [leaderboard/README.md](leaderboard/README.md) to submit results.

---

## Try it in Docker

```bash
git clone https://github.com/RudrenduPaul/agentregress
cd agentregress
docker compose up
```

Runs the basic comparison example inside a container, no local Python setup needed. Good for verifying the install works before wiring it into your own agent.

---

## Security

- **Supply chain:** SLSA Level 2 via GitHub Actions provenance. All releases signed with Sigstore. SBOM attached to every GitHub Release.
- **Vulnerability scanning:** Trivy scans on every CI run (HIGH/CRITICAL only, exit on unfixed). CodeQL static analysis on every push.
- **Dependency pinning:** Dependabot keeps all GitHub Actions and Python dependencies current.
- **Disclosure:** [SECURITY.md](SECURITY.md) — report vulnerabilities privately via GitHub Security Advisories.

---

## Leaderboard

The `leaderboard/` directory version-controls Tau-bench pass^k, GAIA, and SWE-bench results across models and frameworks. Submit by opening a PR with a JSON file matching `leaderboard/schema.json`. Results are independently reproduced before merging.

See [leaderboard/README.md](leaderboard/README.md).

---

## Contributing

- Read [CONTRIBUTING.md](CONTRIBUTING.md) before opening a PR
- Good first issues are labeled in GitHub
- Stats module (`src/agent_regress/stats/`) must stay pure Python + scipy -- no LLM calls, ever
- All PRs require 95% coverage on `stats/`, 90% on `core/` and `ci/`

GitHub Discussions for design questions. Discord for community: discord.gg/agentregress

Apache 2.0. Contributions welcome.

---

*Built by Rudrendu Paul and Sourav Nandy*
