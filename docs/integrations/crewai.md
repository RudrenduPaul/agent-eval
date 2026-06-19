# CrewAI Integration

## Install

```bash
pip install agent-regress[crewai]
```

## Usage

```python
from agent_regress import compare
from agent_regress.integrations.crewai import crewai_runner

crew_v1 = build_crew(agent_config="v1")
crew_v2 = build_crew(agent_config="v2")

def scorer(output: str, test_case: dict) -> float:
    return 1.0 if test_case["expected"].lower() in str(output).lower() else 0.0

report = compare(
    version_a=crewai_runner(crew_v1),
    version_b=crewai_runner(crew_v2),
    test_suite=test_suite,
    n_runs=50,
    scorer=scorer,
)
print(report)
```
