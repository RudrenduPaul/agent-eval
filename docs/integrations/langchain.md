# LangChain LCEL Integration

## Install

```bash
pip install agent-regress-cli[langchain]
```

## Usage

```python
from agent_regress import compare
from agent_regress.integrations.langchain import langchain_runner
from langchain_core.runnables import RunnableLambda

chain_v1 = RunnableLambda(lambda x: x["input"].upper())
chain_v2 = RunnableLambda(lambda x: x["input"].lower())

def scorer(output: str, test_case: dict) -> float:
    return 1.0 if output == test_case["expected"] else 0.0

report = compare(
    version_a=langchain_runner(chain_v1),
    version_b=langchain_runner(chain_v2),
    test_suite=[{"input": "hello", "expected": "HELLO"}],
    n_runs=50,
    scorer=scorer,
)
print(report)
```
