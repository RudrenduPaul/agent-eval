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

## Tool-level runner

Use `crewai_tool_runner()` to exercise a single `BaseTool`/`CrewStructuredTool`
directly, without paying for a full multi-step Crew `kickoff()` to converge.
This isolates tool-only behavioral changes (e.g. output formatting/schema
changes) from the noise of a whole agentic run.

```python
from agent_regress import compare
from agent_regress.integrations.crewai import crewai_tool_runner

tool_v1 = build_tool(output_schema="v1")
tool_v2 = build_tool(output_schema="v2")

# test_case["tool_kwargs"] is passed straight through to tool.run()/tool._run()
test_suite = [
    {"tool_kwargs": {"query": "revenue last quarter"}, "expected": "..."},
]

report = compare(
    version_a=crewai_tool_runner(tool_v1),
    version_b=crewai_tool_runner(tool_v2),
    test_suite=test_suite,
    n_runs=50,
    scorer=scorer,
)
print(report)
```

## kickoff-kwargs passthrough

Pass `kickoff_kwargs` to forward extra keyword arguments to
`crew.kickoff(inputs=inputs, **kickoff_kwargs)` on every call — useful for
comparing the *same* Crew/Flow object under different kickoff-time
parameters (e.g. state restoration) rather than two separately built crews.

```python
from agent_regress import compare
from agent_regress.integrations.crewai import crewai_runner

flow = build_flow()

report = compare(
    version_a=crewai_runner(flow, kickoff_kwargs={"restore_from_state_id": None}),
    version_b=crewai_runner(flow, kickoff_kwargs={"restore_from_state_id": checkpoint_id}),
    test_suite=test_suite,
    n_runs=50,
    scorer=scorer,
)
print(report)
```

## Avoiding shared-state corruption with `crew_factory`

`run_suite()` (used internally by `compare()`) parallelizes across test
cases with `max_workers=None` (unbounded) by default. If your Crew has
**memory, knowledge, or RAG enabled**, that store is Crew-level shared,
mutable state — reusing one `Crew` object across concurrent test-case
executions (the default `crew=` mode) can interleave reads/writes on that
store and corrupt your comparison's independence assumption, producing
noise that looks like a regression but isn't.

Pass `crew_factory` instead of `crew` so a fresh Crew (and fresh shared
state) is built for every invocation:

```python
from agent_regress import compare
from agent_regress.integrations.crewai import crewai_runner

report = compare(
    version_a=crewai_runner(crew_factory=lambda: build_crew(config="v1")),
    version_b=crewai_runner(crew_factory=lambda: build_crew(config="v2")),
    test_suite=test_suite,
    n_runs=50,
    scorer=scorer,
)
print(report)
```

Alternatively, keep `crew=` but serialize execution with
`run_suite(..., max_workers=1)` (or pass `max_workers=1` through your own
`compare()`/`run_suite()` call) to avoid concurrent access to the shared
Crew instance entirely.
