# Changelog

All notable changes documented here.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Versions follow [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.5] - 2026-07-20

### Added

- `npm/`: the `agent-regress-npm-cli` wrapper source is now tracked in this repo (previously it existed only on the npm registry, unrecoverable from source control); republished in sync at 0.1.5 with the Python package, added Sourav Nandy as a listed contributor for author parity with PyPI
- `release.yml`'s `PYPI_TOKEN` repo secret is now configured, so the tag-triggered PyPI publish step is functional for the first time

### Fixed

- `agent_regress.__version__` (and `agent-regress --version`) was hardcoded to `0.1.2` and had drifted two releases behind `pyproject.toml`; now derived dynamically from installed package metadata via `importlib.metadata.version()` so it can't drift again
- The `v0.1.4` GitHub Release/tag was cut against the wrong commit (still `0.1.3` in `pyproject.toml`) and has been deleted and re-cut correctly as `v0.1.5`
- `.github/workflows/benchmark.yml` pinned `benchmark-action/github-action-benchmark` to a SHA that does not exist upstream, failing every push; repinned to the real `v1.20.4` commit
- README: clarified that `compare()`'s low-power warning (`n < 50`) and `RegressionGate`'s CI-gate warning (`n < 30`) are two intentionally different, independent thresholds, not a documentation inconsistency
- README: PyPI 0.1.4's published long description was built before that session's README edits landed and was missing the CLI quickstart section; 0.1.5 republishes with the current README
- Added a README caveat for the `[crewai]` extra's unpatched critical `chromadb` CVE (GHSA-f4j7-r4q5-qw2c, no upstream fix yet)

### Correction

- This entry originally claimed the transitive `json-repair` dependency (GHSA-xf7x-x43h-rpqh) was bumped past its high-severity advisory. That did not actually happen: `crewai` pins `json-repair~=0.25.2` (confirmed against crewai 1.15.4 and the current latest, 1.15.5), which caps resolution below the 0.60.1 fix — `uv.lock` is still on `json-repair==0.25.3` and the Dependabot alert remains open. As established during the original triage, the vulnerable function doesn't exist in 0.25.3, so this is believed non-exploitable as installed, but it is not fixed, and won't be until `crewai` itself relaxes that pin.

## [0.1.4] - 2026-07-20

### Changed

- PyPI `Development Status` classifier raised from `3 - Alpha` to `4 - Beta`
- PyPI/`pyproject.toml` `description` rewritten to lead with the p-value/distributional-shift framing and note the project has no SaaS dependency
- PyPI keywords expanded for search discoverability (`p-value`, `cohen-d`, `mann-whitney`, `langgraph`, `openai-agents`, `crewai`, `promptfoo-alternative`, `eval`, `benchmark`, `ci-cd`)
- README rewritten to lead with the regression-detection problem statement, move the framework comparison table above the fold (renamed "Why not DeepEval, Promptfoo, or Braintrust?"), and add a CLI-first quickstart ahead of the Python API example
- Added `docs/pr-analysis.md`: real merged-PR case studies (LangGraph, OpenAI Agents SDK, CrewAI) where distributional testing catches regressions threshold testing misses

## [0.1.2] - 2026-07-16

### Added

- PyPI distribution renamed to `agent-regress-cli` (import path is unchanged: `import agent_regress`) -- `agent-regress` on PyPI was blocked as too similar to an existing unrelated project
- `agent-regress` CLI (`src/agent_regress/cli.py`), wired up via `[project.scripts]`
- `agent-regress compare --version-a-results <path.json> --version-b-results <path.json>` -- file-based entry point that runs two JSON arrays of pre-computed per-run scores through the same Mann-Whitney U / bootstrap CI / Cohen's d pipeline `compare()` uses
- `--json` flag on `compare` for clean, machine-readable `Report` output (warnings routed to stderr)
- `--fail-on-regression` flag on `compare` for CI use (exit 1 on a `REGRESSED` verdict)
- `agent-regress --version`

### Fixed

- `mann_whitney_u`: raise `ValueError` on NaN input instead of silently returning `p=1.0`
- `rank_biserial_r`: propagate `nan` instead of silently returning `-1.0` on NaN input
- `run_suite`: warn threshold raised from n<10 to n<30 to match recommendation message
- `_get_expected`: fix `KeyError` when `expected` key is present but set to `None`
- `f1_scorer`: use `Counter` multiset intersection instead of set intersection — fixes wrong F1 when tokens repeat
- `compare`: align `_MIN_N_WARN` threshold (was 30, now 50) with warning message and `n_runs` default
- `compare` / `Report`: store `p_threshold` and `min_effect` on `Report` so `assert_stable()` uses the right defaults
- `gaia.py`: fix false-positive accuracy when agent raises and `expected_answer` is `'none'`
- `tau_bench.py`: raise clear `ValueError` on empty `k_values` instead of opaque `max()` error
- `langchain` / `langgraph` integrations: fix fallback adapters that were wrapping `test_case` in a nested dict
- `openai_agents_runner`: narrow `RuntimeError` catch to avoid masking real errors and double-invoking the agent
- `benchmarks/__init__`: export `GAIALevelResult`, `SWEBenchResult`, `TauBenchResult`
- `core/__init__` / top-level `__init__`: export `AgentCallable` and `ScorerCallable` type aliases
- PyPI `Author` field linked to Rudrendu's personal email under Sourav's displayed name; authors are now name-only with GitHub profile links in `project.urls`

## [0.1.0] - 2026-06-19

### Added

- `compare(version_a, version_b, test_suite, n_runs=50)` -- primary public API
- `run_suite(agent, test_suite, n_runs)` -- run agent N times on a test suite
- `Report` dataclass with `verdict`, `p_value`, `effect_size`, `ci_lower`, `ci_upper`
- `Verdict` enum: `REGRESSED`, `STABLE`, `IMPROVED`, `INSUFFICIENT_DATA`
- Mann-Whitney U test with continuity correction (`stats.mann_whitney_u`)
- Bootstrap confidence intervals at 95%, N=1000 resamples (`stats.bootstrap_mean_ci`)
- Cohen's d and rank-biserial r effect size (`stats.compute_effect_sizes`)
- `RegressionGate` and `assert_no_regression` for pytest CI integration
- `exact_match_scorer` and `f1_scorer` built-in scorers
- LangGraph integration (`integrations.langgraph_runner`)
- LangChain LCEL integration (`integrations.langchain_runner`)
- OpenAI Agents SDK integration (`integrations.openai_agents_runner`)
- CrewAI integration (`integrations.crewai_runner`)
- Tau-bench pass^k harness (`benchmarks.TauBenchHarness`)
- GAIA Level 1-3 split harness (`benchmarks.GAIAHarness`)
- SWE-bench Verified scaffold score harness (`benchmarks.SWEBenchHarness`)
- Docker Compose self-host setup
- Sample size warnings: warns (not fails) when n < 30 per version
- Apache 2.0 license
- OpenSSF Scorecard CI workflow
- SLSA Level 2 release signing via Sigstore
- SBOM generation on release (CycloneDX JSON format)
