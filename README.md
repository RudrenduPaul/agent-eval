# Agent Evaluation

**Statistical regression testing for LLM agents.** Run your agent 50 times on a fixed test suite at version A, 50 times at version B, and get a p-value on whether behavior actually changed, not just whether the score looks different.

```
$ uv run python examples/01-basic-comparison/example.py

============================================================
agent-regress Report -- tool_accuracy
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

[![PyPI](https://img.shields.io/pypi/v/agent-regress)](https://pypi.org/project/agent-regress/)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![CI](https://github.com/RudrenduPaul/agent-eval/actions/workflows/ci.yml/badge.svg)](https://github.com/RudrenduPaul/agent-eval/actions/workflows/ci.yml)

[![OpenSSF Scorecard](https://api.securityscorecards.dev/projects/github.com/RudrenduPaul/agent-eval/badge)](https://api.securityscorecards.dev/projects/github.com/RudrenduPaul/agent-eval)

---

## Install

```bash
pip install agent-regress
# or
uv add agent-regress
```

---

## The problem this solves

You changed a prompt. Or switched from GPT-4o to GPT-4o-mini to cut costs. Or a dependency updated silently. Your evals still pass, because they test individual responses against fixed thresholds. They don't detect whether behavior shifted across the whole distribution.

A 3-point drop in accuracy might be noise from LLM variance. Or it might be a real regression. Without statistical testing you cannot tell which. Teams either ignore small drops and miss real problems, or escalate everything and drown in false alarms.

Agent Evaluation answers the distributional question with a p-value and effect size:

```
============================================================
agent-regress Report -- tool_accuracy
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

DeepEval, Promptfoo, and Braintrust test whether individual responses meet thresholds. None of them answer whether a version's behavior distribution shifted significantly from the last. Agent Evaluation addresses that specific statistical question, which threshold testing cannot answer.

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
    metric="tool_accuracy",  # use any name except "accuracy" when agents return floats
)

print(report)           # structured output with p-value, CI, effect size
report.assert_stable()  # raises AssertionError if behavior regressed
```

Agent returns text? Pass a scorer or use the built-ins:

```python
from agent_regress import compare, exact_match_scorer, f1_scorer

# exact_match_scorer: 1.0 if str(output).strip() == str(expected).strip()
# f1_scorer: token-level F1 (multiset — handles repeated tokens correctly)
report = compare(
    version_a=agent_v1,
    version_b=agent_v2,
    test_suite=test_suite,
    n_runs=50,
    scorer=exact_match_scorer,  # test_case must have an "expected" key
)
```

Or write your own:

```python
def my_scorer(output: str, test_case: dict) -> float:
    return 1.0 if output.strip() == test_case["expected"] else 0.0

report = compare(..., scorer=my_scorer)
```

---

## Add to CI: fail the build on regression

Two patterns. Pick one.

**`report.assert_stable()`** — inline, after you've already called `compare()`:

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

**`RegressionGate`** — reusable gate object, useful when you run multiple comparisons with the same thresholds:

```python
from agent_regress import compare, RegressionGate

gate = RegressionGate(p_threshold=0.05, min_effect=0.2)

def test_tool_accuracy():
    report = compare(version_a=prod, version_b=staging, test_suite=suite, n_runs=50)
    gate.check(report)  # raises AssertionError on regression; warns if n < 30

def test_routing_accuracy():
    report = compare(version_a=prod, version_b=staging, test_suite=routing_suite, n_runs=50)
    gate.check(report)
```

Both patterns: warn (not fail) when `n < 30` per version; treat `n < 10` as insufficient data and skip the gate.

```bash
uv run pytest test_regression.py
```

---

## How it differs from the alternatives

| Capability | Agent Evaluation | DeepEval | Braintrust | Promptfoo |
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

DeepEval tests whether an individual agent response clears a quality bar. Agent Evaluation tests whether behavior changed significantly between two agent versions, a different statistical question that threshold testing cannot answer. The scipy Mann-Whitney U call at the core is one line, so any SaaS eval platform can add it. What accumulates over time through production use is version-specific regression history and a community-maintained benchmark leaderboard with independent result verification.

---

## Statistical methods

Agent Evaluation uses three statistical tests, applied in combination:

**Mann-Whitney U** compares two score distributions without assuming normality. LLM scores are not Gaussian. The U test is distribution-free and robust to the long tails and bimodal distributions that appear in real agent outputs.

**Bootstrap confidence intervals** (1,000 resamples, seed=42) give a 95% CI on the mean score delta. The CI tells you how large the shift was: a CI of [-0.22, -0.07] means you can be 95% confident the true per-run accuracy drop is between 7 and 22 percentage points.

**Cohen's d** (pooled standard deviation) separates statistical significance from operational significance. A shift at p=0.001 with d=0.04 is real but meaningless. A shift at p=0.06 with d=0.5 is operationally large but requires more data to confirm. The default CI gate acts only when both p < 0.05 and d >= 0.2.

See [docs/statistical-methods.md](docs/statistical-methods.md) for the full methodology.

---

## Benchmarks

Statistical test overhead is the time to run the comparison itself, not the agent calls. Agent calls are the bottleneck; the statistics are not.

Measured on Apple M3 Pro, Python 3.14, scipy 1.15, numpy 2.2:

| Operation | n=50 per version | n=1,000 per version |
|---|---|---|
| Mann-Whitney U | **0.34ms** | **0.47ms** |
| Bootstrap CI (1,000 resamples) | **26ms** | **31ms** |
| Full compare() statistical overhead | **~27ms** | **~32ms** |

See [docs/benchmarks.md](docs/benchmarks.md) to reproduce.

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

Agent Evaluation ships harnesses for the three standard agent benchmarks:

**Tau-bench pass^k** measures reliability across k independent attempts. Single-run benchmarks miss degradation: an agent that succeeds 65% of the time at k=1 reaches 97% at k=8. The k=1 vs k=8 curve is the signal.

```python
from agent_regress.benchmarks.tau_bench import TauBenchHarness

harness = TauBenchHarness(agent=my_agent, dataset=tau_bench_dataset)
results = harness.evaluate(k_values=[1, 4, 8])
```

**GAIA Level 1-3 split** stratifies by task difficulty. Overall accuracy hides per-difficulty regressions: a prompt change that helps Level 1 often hurts Level 3.

```python
from agent_regress.benchmarks.gaia import GAIAHarness

harness = GAIAHarness(agent=my_agent, dataset=gaia_dataset)
results = harness.evaluate()  # returns list[GAIALevelResult], one per level
for r in results:
    print(f"Level {r.level}: {r.accuracy:.3f}  ({r.n_correct}/{r.n_questions})")
```

**SWE-bench scaffold score** isolates framework contribution from model contribution.

```python
from agent_regress.benchmarks.swebench import SWEBenchHarness

harness = SWEBenchHarness(agent=my_agent, dataset=swe_dataset)
result = harness.evaluate()
print(f"scaffold pass rate: {result.scaffold_pass_rate:.3f}  ({result.n_resolved}/{result.n_instances})")
```

See [leaderboard/README.md](leaderboard/README.md) to submit results.

---

## Try it in Docker

```bash
git clone https://github.com/RudrenduPaul/agent-eval
cd agent-eval
docker compose up
```

Starts two services:

- **web** (`http://localhost:8080`) — leaderboard UI served by `web/serve.py`, reading `leaderboard/results/*.json`
- **example** — runs `examples/01-basic-comparison/example.py` and prints the comparison report to stdout

Good for verifying the install works and seeing the leaderboard UI before wiring agent-regress into your own agent.

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
- Stats module (`src/agent_regress/stats/`) must stay pure Python + scipy — no LLM calls, ever
- All PRs require 95% coverage on `stats/`, 80% overall

GitHub Discussions for design questions.

Apache 2.0. Contributions welcome.

---

## Cite this work

If you use Agent Evaluation in research, please cite:

```bibtex
@software{paul2026agenteval,
  author = {Paul, Rudrendu and Nandy, Sourav},
  title = {Agent Evaluation: Statistical Regression Testing for LLM Agents},
  year = {2026},
  url = {https://github.com/RudrenduPaul/agent-eval},
  license = {Apache-2.0}
}
```

Methodology: [docs/arxiv-preprint-draft.md](docs/arxiv-preprint-draft.md).

---

*Built by Rudrendu Paul and Sourav Nandy*
