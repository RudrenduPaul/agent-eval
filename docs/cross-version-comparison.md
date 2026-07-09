# Cross-Environment / Cross-Version Comparison

Every integration in `agent_regress.integrations.*` wraps a live,
already-imported object (a `Crew`, a compiled LangGraph graph, an OpenAI
Agents SDK `Agent`, ...) as an `AgentCallable` inside the *current* Python
process. That's fine for comparing two configurations of the same installed
package version, but it cannot compare two different *installed versions* of
the same package -- a single interpreter only ever has one `crewai` (or
`langgraph`, or any other package) importable via `sys.modules` at a time.

`subprocess_runner()` closes that gap. It builds an `AgentCallable` that
shells out to a separate Python interpreter (e.g. the `python` inside a venv
pinned to `crewai==0.60.0`) for every single call, so `version_a` can be
backed by one installed package version and `version_b` by a completely
different one.

This is the pattern to reach for whenever the comparison is literally
"package version A vs package version B" -- for example, validating a
version-bump PR before merging it, or reproducing a regression that only
shows up on a specific pinned release.

## How `compare()` stays agnostic to this

`compare(version_a=..., version_b=..., ...)` only requires `version_a` and
`version_b` to be `AgentCallable`s -- plain `dict -> Any` callables. Nothing
in `compare()` or `run_suite()` inspects *how* that callable produces its
result, so an `AgentCallable` that shells out to a subprocess is exactly as
valid an argument as one that calls an in-process object directly. No
changes to `compare()` were needed to support this.

## The stdin/stdout JSON contract

`subprocess_runner(python_executable, script_path, timeout=None)` runs
`[python_executable, script_path]` as a subprocess for every test case. The
target script must:

1. Read a single JSON object (the test case) from stdin.
2. Print a single JSON-serializable value to stdout -- and nothing else.
   Any extra `print()` calls in the script will corrupt the `json.loads()`
   parse on the caller side, since `subprocess_runner` reads the entire
   captured stdout as one JSON document.

If the subprocess exits with a non-zero return code, `subprocess_runner`
raises `RuntimeError` with the captured stderr included in the message, so
failures inside the pinned-version environment surface clearly instead of
being silently swallowed.

## Example: comparing two pinned CrewAI versions

Two isolated venvs, each with a different `crewai` version installed:

```bash
python -m venv /path/to/venvA && /path/to/venvA/bin/pip install "crewai==0.60.0"
python -m venv /path/to/venvB && /path/to/venvB/bin/pip install "crewai==0.63.0"
```

`runner_a.py` (identical in shape to `runner_b.py`, just pointed at a
different venv):

```python
# runner_a.py -- run with venvA's python, which has crewai==0.60.0 installed
import sys
import json

from crewai import Agent, Crew, Task

def build_crew() -> Crew:
    researcher = Agent(
        role="Researcher",
        goal="Answer the user's query accurately",
        backstory="An experienced research analyst.",
    )
    task = Task(
        description="{query}",
        expected_output="A concise, accurate answer.",
        agent=researcher,
    )
    return Crew(agents=[researcher], tasks=[task])

def main() -> None:
    test_case = json.loads(sys.stdin.read())
    crew = build_crew()
    result = crew.kickoff(inputs={"query": test_case["query"]})
    print(json.dumps({"output": str(result)}))

if __name__ == "__main__":
    main()
```

`runner_b.py` is the same script, unchanged, except it runs under venvB's
`python` -- so it picks up `crewai==0.63.0` from that venv's
`site-packages` instead. The comparison isolates the package version as the
only variable.

## Wiring it into `compare()`

```python
from agent_regress import compare
from agent_regress.core.runner import subprocess_runner

def scorer(output: dict, test_case: dict) -> float:
    return 1.0 if test_case["expected"].lower() in str(output["output"]).lower() else 0.0

report = compare(
    version_a=subprocess_runner("/path/to/venvA/bin/python", "runner_a.py"),
    version_b=subprocess_runner("/path/to/venvB/bin/python", "runner_b.py"),
    test_suite=test_suite,
    n_runs=50,
    scorer=scorer,
)
print(report)
```

Each of the `n_runs * len(test_suite)` calls spawns a fresh subprocess
against the pinned interpreter for that version, so `version_a`'s scores
reflect `crewai==0.60.0`'s behavior end-to-end and `version_b`'s reflect
`crewai==0.63.0`'s, with no shared process state between them.

## Performance note

Because each call pays full Python interpreter startup cost, subprocess-based
comparisons are substantially slower per call than an in-process
`AgentCallable`. Prefer subprocess isolation specifically for the
cross-version case (where it's the only option), and use the direct
integration wrappers (`crewai_runner()`, `langgraph_runner()`, etc.) for
same-version, same-process comparisons where they apply.

## Timeouts

Pass `timeout=` (seconds) to bound how long any single subprocess call is
allowed to run. If the script hangs or an underlying agent call never
returns, `subprocess_runner` raises `subprocess.TimeoutExpired` instead of
blocking `run_suite()`'s worker thread indefinitely.

```python
subprocess_runner("/path/to/venvA/bin/python", "runner_a.py", timeout=30.0)
```
