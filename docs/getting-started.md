# Getting Started

From zero to a working regression gate in under 10 minutes.

---

## Step 1: Install

```bash
pip install agent-regress
```

Verify:

```bash
python -c "from agent_regress import compare; print('OK')"
```

## Step 2: Your first comparison

```python
from agent_regress import compare
import random

# Simulate two agent versions -- replace with your real agent callables
def agent_v1(test_case: dict) -> float:
    rng = random.Random(hash(str(test_case)))
    return max(0.0, min(1.0, rng.gauss(0.82, 0.05)))

def agent_v2(test_case: dict) -> float:
    rng = random.Random(hash(str(test_case)) + 500)
    return max(0.0, min(1.0, rng.gauss(0.68, 0.08)))

test_suite = [
    {"query": "find product SKU for order 1001", "expected": "SKU-4001"},
    {"query": "find product SKU for order 1002", "expected": "SKU-4002"},
    {"query": "find product SKU for order 1003", "expected": "SKU-4003"},
]

report = compare(
    version_a=agent_v1,
    version_b=agent_v2,
    test_suite=test_suite,
    n_runs=50,
    metric="tool_accuracy",  # use any non-"accuracy" name when agents return floats
)

print(report)
```

Output:

```
============================================================
agent-regress Report -- tool_accuracy
============================================================
Verdict:    REGRESSED
p-value:    0.0000
Cohen's d:  -3.709
95% CI:     [-0.126, -0.112]

Version A:  0.7918 +/- 0.0264  (n=150)
Version B:  0.6728 +/- 0.0370  (n=150)
Delta:      -0.1191
============================================================
```

## Step 3: CI gate

In your pytest test suite:

```python
# tests/test_regression.py
from agent_regress import compare
from my_agent import production_agent, staging_agent

TEST_SUITE = [{"query": "...", "expected": "..."}, ...]

def test_no_regression():
    report = compare(
        version_a=production_agent,
        version_b=staging_agent,
        test_suite=TEST_SUITE,
        n_runs=50,
    )
    report.assert_stable()  # raises AssertionError if REGRESSED
```

```bash
pytest tests/test_regression.py -v
```

## Step 4: Agent returns text?

Pass a scorer:

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

## Step 5: Framework integrations

LangGraph:

```bash
pip install agent-regress[langgraph]
```

```python
from agent_regress import compare
from agent_regress.integrations.langgraph import langgraph_runner

report = compare(
    version_a=langgraph_runner(graph_v1),
    version_b=langgraph_runner(graph_v2),
    test_suite=test_suite,
    n_runs=50,
)
```

OpenAI Agents SDK:

```bash
pip install agent-regress[openai-agents]
```

```python
from agent_regress.integrations.openai_agents import openai_agents_runner

report = compare(
    version_a=openai_agents_runner(agent_v1),
    version_b=openai_agents_runner(agent_v2),
    test_suite=test_suite,
    n_runs=50,
)
```

---

## Reading the output

| Verdict | What it means | What to do |
|---|---|---|
| STABLE | Distributions not significantly different | Safe to deploy |
| REGRESSED | Version B scored significantly lower (p < 0.05, d ≥ 0.2) | Block the deploy |
| IMPROVED | Version B scored significantly higher | Deploy with confidence |
| INSUFFICIENT_DATA | Fewer than 10 total scores | Increase n_runs or test suite size |

## Tuning the gate

```python
report.assert_stable(
    p_threshold=0.01,  # require stronger statistical evidence
    min_effect=0.5,    # only block on medium+ effects (Cohen's d ≥ 0.5)
)
```

Default: p < 0.05 and Cohen's d ≥ 0.2.

---

## Common issues

**"n_runs too small" warning** — Use n_runs ≥ 30 per version for reliable results. Use n_runs ≥ 50 for production CI gates.

**Scores outside [0.0, 1.0]** — agent-eval clamps and warns. Ensure your scorer returns values in [0.0, 1.0].

**INSUFFICIENT_DATA** — Fewer than 10 scores per group. Increase n_runs or add test cases.

---

## Next steps

- [concepts.md](concepts.md) -- What "statistical regression" means and what it does not
- [statistical-methods.md](statistical-methods.md) -- The full methodology
- [examples/](../examples/) -- Runnable examples for common scenarios
