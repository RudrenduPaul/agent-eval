# Benchmarks

Every number in the main README is reproducible from this directory.

## Run all

```bash
uv sync --extra dev
uv run pytest benchmarks/ -v
```

## Statistical overhead

**File:** `test_stat_overhead.py`

Time to run Mann-Whitney U, bootstrap CI, and Cohen's d. This is the statistical layer
overhead -- not the agent calls.

Expected on M-series Mac or GitHub Actions ubuntu-latest:
- Mann-Whitney U on n=1000: less than 5ms
- Bootstrap CI on n=1000 (1000 resamples): less than 50ms
- Full statistical overhead: less than 60ms for n=1000 per version

```bash
uv run pytest benchmarks/test_stat_overhead.py --benchmark-only -v
```

## Tau-bench pass^k

**File:** `test_tau_bench.py`

Demonstrates pass^k at k=1, 4, 8. The mock agent uses a configurable success probability.

A mock agent at 60% single-attempt success shows:
- pass^1 approximately 0.60
- pass^4 approximately 0.97
- pass^8 approximately 0.999

To use with a real agent: replace `_mock_agent()` with your agent callable.

## GAIA Level 1-3

**File:** `test_gaia.py`

Accuracy stratified by difficulty level. A tool that scores 80% on Level 1 and 20% on Level 3
is very different from one that scores 50% uniformly.

## SWE-bench scaffold

**File:** `test_swebench.py`

The evaluation harness contribution to SWE-bench pass rate. Replace the mock agent
with a real code-generation agent to measure scaffold lift.
