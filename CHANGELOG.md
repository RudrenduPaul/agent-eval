# Changelog

All notable changes documented here.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Versions follow [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
