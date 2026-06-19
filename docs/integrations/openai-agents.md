# OpenAI Agents SDK Integration

## Install

```bash
pip install agent-regress[openai-agents]
```

## Usage

```python
from agent_regress import compare
from agent_regress.integrations.openai_agents import openai_agents_runner

# Your OpenAI Agents SDK agent instances
agent_v1 = build_agent(instructions="v1 instructions")
agent_v2 = build_agent(instructions="v2 instructions")

def scorer(output: str, test_case: dict) -> float:
    return 1.0 if test_case["expected"] in output else 0.0

report = compare(
    version_a=openai_agents_runner(agent_v1),
    version_b=openai_agents_runner(agent_v2),
    test_suite=test_suite,
    n_runs=50,
    scorer=scorer,
)
print(report)
```
