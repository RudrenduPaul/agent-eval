# Getting Started

## Install

```bash
pip install agent-regress
```

## Your first comparison

```python
from agent_regress import compare

def agent_v1(test_case: dict) -> float:
    # return 1.0 for correct, 0.0 for wrong
    return 1.0 if test_case.get("expected") == "Paris" else 0.0

def agent_v2(test_case: dict) -> float:
    return 1.0 if test_case.get("expected") == "Paris" else 0.0

test_suite = [
    {"query": "Capital of France?", "expected": "Paris"},
    {"query": "Capital of Japan?", "expected": "Tokyo"},
]

report = compare(
    version_a=agent_v1,
    version_b=agent_v2,
    test_suite=test_suite,
    n_runs=50,
)
print(report)
```

## Set up a CI gate

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
    report.assert_stable()
```

Run with: `pytest test_regression.py`

## LangGraph integration

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

## Reading the report

- **STABLE** (p=0.41): Distributions are not significantly different. Safe to deploy.
- **REGRESSED** (p=0.003, d=-0.61): Version B scored significantly lower. Block the deploy.
- **IMPROVED** (p=0.01, d=0.45): Version B scored significantly higher.
- **INSUFFICIENT_DATA**: Fewer than 10 total scores. Cannot compute statistics.
