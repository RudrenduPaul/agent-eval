# LangGraph Integration

## Install

```bash
pip install agent-regress[langgraph]
```

## Usage

```python
from agent_regress import compare
from agent_regress.integrations.langgraph import langgraph_runner

# Build your graphs
graph_v1 = build_graph(model="gpt-4o", prompt_version="v1")
graph_v2 = build_graph(model="gpt-4o", prompt_version="v2")

def scorer(output: dict, test_case: dict) -> float:
    return 1.0 if output.get("answer") == test_case["expected"] else 0.0

report = compare(
    version_a=langgraph_runner(graph_v1),
    version_b=langgraph_runner(graph_v2),
    test_suite=test_suite,
    n_runs=50,
    scorer=scorer,
)
print(report)
report.assert_stable()
```
