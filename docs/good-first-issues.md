# Good First Issues — Paste to GitHub

These 20 issues are ready to create on GitHub before the public launch. Create them labeled `good first issue` and `help wanted`. Each has a self-contained scope.

---

## Issue 1: Add `--n-runs` CLI argument

**Labels:** `good first issue`, `enhancement`

agentregress currently requires Python code to run comparisons. Add a lightweight CLI entry point that reads two JSONL files (each containing agent outputs as floats) and runs the statistical comparison without writing Python.

```bash
agentregress compare --a outputs_v1.jsonl --b outputs_v2.jsonl --metric tool_accuracy
```

Files should contain one float score per line. This is a purely additive change -- no existing API changes needed.

**Files:** `src/agent_regress/cli.py` (new), `pyproject.toml` (add `[project.scripts]`)

---

## Issue 2: Add `weighted_f1_scorer` built-in scorer

**Labels:** `good first issue`, `enhancement`

The current `f1_scorer` in `scorer.py` uses binary token overlap. Add a `weighted_f1_scorer` that handles multi-class prediction tasks by computing the weighted average F1 across class labels.

**Files:** `src/agent_regress/core/scorer.py`, `tests/unit/core/test_scorer.py`

---

## Issue 3: Add `semantic_similarity_scorer` (optional, requires sentence-transformers)

**Labels:** `good first issue`, `enhancement`

Add a scorer that computes cosine similarity between agent output and expected answer using sentence-transformers embeddings. Should be an optional dependency and lazy-imported.

```python
from agent_regress.scorers import semantic_similarity_scorer
```

**Files:** `src/agent_regress/scorers/` (new submodule), `pyproject.toml` (add `st` optional dep)

---

## Issue 4: Add `Report.to_dict()` and `Report.to_json()` methods

**Labels:** `good first issue`, `enhancement`

The `Report` dataclass has a `__str__` method but no structured serialization. Add `to_dict()` returning a plain dict and `to_json()` returning a JSON string. Both should round-trip through `Report.from_dict()`.

**Files:** `src/agent_regress/core/report.py`, `tests/unit/core/test_report.py`

---

## Issue 5: Reproduce README benchmark numbers and update if different

**Labels:** `good first issue`, `documentation`, `benchmark`

Clone the repo, run `uv run pytest benchmarks/test_stat_overhead.py --benchmark-only -v` on your hardware, and compare to the numbers in `benchmarks/README.md`. If your numbers differ significantly (more than 2x), open a PR updating the table to include a "GitHub Actions ubuntu-latest" column.

**Expected output format in PR:** add a second column to the table in `benchmarks/README.md` with your hardware and measured numbers.

---

## Issue 6: Add LangChain LCEL integration example

**Labels:** `good first issue`, `documentation`

`docs/integrations/langchain.md` is brief. Write a complete working example using LangChain LCEL that compares two chains (different prompts or models) using `langgraph_runner`. Should be runnable with `pip install agent-regress[langchain]` and a real OpenAI API key.

**Files:** `docs/integrations/langchain.md`, `examples/05-langchain-lcel/`

---

## Issue 7: Add `parallel_compare()` for independent test suite shards

**Labels:** `good first issue`, `enhancement`

For large test suites (1,000+ cases), running them sequentially is slow. Add `parallel_compare()` that shards the test suite across N workers and combines results before statistical testing. Use `concurrent.futures.ThreadPoolExecutor` (not multiprocessing, to keep compatibility with LLM clients that are not fork-safe).

**Files:** `src/agent_regress/core/compare.py`, `tests/unit/core/test_compare.py`

---

## Issue 8: Add `min_runs_for_power()` utility function

**Labels:** `good first issue`, `enhancement`

Add a utility that computes the minimum N per version required for 80% power to detect a given effect size at a given significance level. Uses the Mann-Whitney U power formula.

```python
from agent_regress.stats import min_runs_for_power
n = min_runs_for_power(effect_size=0.2, alpha=0.05, power=0.8)  # returns ~200
```

**Files:** `src/agent_regress/stats/power.py` (new), `src/agent_regress/stats/__init__.py`, `tests/unit/stats/test_power.py`

---

## Issue 9: Submit a real leaderboard result

**Labels:** `good first issue`, `leaderboard`

Run one of the benchmark harnesses against a real model (GPT-4o-mini is the cheapest option) and submit the results as a JSON file in `leaderboard/results/`. Full instructions in `leaderboard/README.md`. CI validates schema automatically. Estimated cost: less than $5 of API credits.

**Files:** `leaderboard/results/<your-model>-<date>.json`

---

## Issue 10: Add mypy type stubs for the CLI (Issue 1 follow-up)

**Labels:** `good first issue`, `typing`

Once Issue 1 (CLI) is merged, add `py.typed` compliance for the CLI module and ensure `mypy src/ --strict` passes with the CLI code. This is a follow-up issue that depends on Issue 1.

---

## Issue 11: Add `Report.plot()` using matplotlib (optional dependency)

**Labels:** `good first issue`, `enhancement`

Add a `plot()` method to `Report` that generates a side-by-side histogram of the two score distributions with vertical lines at the means. Requires `matplotlib` as an optional dependency.

```python
report.plot(save_to="regression_report.png")
```

**Files:** `src/agent_regress/core/report.py`, `pyproject.toml`

---

## Issue 12: Add `CrewAI` integration example

**Labels:** `good first issue`, `documentation`

`docs/integrations/crewai.md` is empty. Write a complete working example using CrewAI that wraps a simple crew in `crewai_runner` and compares two crew configurations. Should be runnable with `pip install agent-regress[crewai]`.

**Files:** `docs/integrations/crewai.md`, `examples/06-crewai/`

---

## Issue 13: Add `--export-report` flag to CLI (depends on Issue 1 and Issue 4)

**Labels:** `good first issue`, `enhancement`

Once Issue 1 (CLI) and Issue 4 (Report serialization) are merged, add `--export-report report.json` to the CLI that writes the full Report as JSON after a comparison run.

---

## Issue 14: Test on Windows and document any compatibility issues

**Labels:** `good first issue`, `testing`, `documentation`

agentregress is tested on Linux and macOS. Run the unit tests on Windows (`uv run pytest tests/unit/ -q`) and document any failures. If tests pass: open a PR adding `windows-latest` to the CI matrix. If they fail: open an issue with the specific failure mode.

---

## Issue 15: Add `conftest.py` fixtures for the standard benchmark test suites

**Labels:** `good first issue`, `testing`

Currently each test file creates its own test suite. Add a `conftest.py` in `tests/` that provides standard fixtures for common benchmark scenarios (10-case suite, 50-case suite, multi-metric suite). Refactor existing tests to use these fixtures where appropriate.

**Files:** `tests/conftest.py`, multiple test files

---

## Issue 16: Write integration test for LangGraph (requires API key)

**Labels:** `good first issue`, `integration-tests`

`tests/integration/test_langgraph.py` exists but is minimal. Write a full integration test that runs two LangGraph graphs (different prompts) against the real OpenAI API and verifies that `compare()` produces a valid Report. Tag with `@pytest.mark.integration`.

**Files:** `tests/integration/test_langgraph.py`

---

## Issue 17: Add `GAIA_DATASET_PATH` environment variable support

**Labels:** `good first issue`, `enhancement`

The GAIA harness currently requires the path to be passed as an argument. Add support for `GAIA_DATASET_PATH` environment variable as a fallback, consistent with how most CLI tools handle dataset paths.

**Files:** `src/agent_regress/benchmarks/gaia.py`

---

## Issue 18: Add progress bar to `compare()` using `rich`

**Labels:** `good first issue`, `enhancement`

`rich` is already a dependency. Add an optional progress bar to `compare()` that shows how many of the N × M runs have completed. Should be enabled by default but suppressible with `verbose=False`.

**Files:** `src/agent_regress/core/runner.py`, `src/agent_regress/core/compare.py`

---

## Issue 19: Translate README to Japanese or Chinese

**Labels:** `good first issue`, `documentation`, `i18n`

The Japanese and Chinese ML communities are significant consumers of OSS eval tools. Translate the README to either Japanese (`README.ja.md`) or Chinese (`README.zh.md`). The translated version should be accurate technical translation, not machine-translated output.

---

## Issue 20: Add a Jupyter notebook example

**Labels:** `good first issue`, `documentation`

Researchers often work in Jupyter notebooks. Add `examples/07-jupyter-notebook/agentregress-demo.ipynb` that walks through the basic comparison workflow step by step. Should produce the same structured output as example 01.

---

*Create all 20 on GitHub before the public launch. Each is independently completable in 2-4 hours.*
