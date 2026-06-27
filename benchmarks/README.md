# Benchmarks

Every number in the main README is reproducible from this directory.

## Run all

```bash
uv sync --extra dev
uv run pytest benchmarks/ -v
```

---

## Statistical overhead (`test_stat_overhead.py`)

Time for the statistical layer only -- not the agent calls. Agent calls dominate; the statistics are not the bottleneck.

**Measured on Apple M3 Pro, Python 3.14, scipy 1.15, numpy 2.2:**

| Operation | n=50 per version | n=1,000 per version |
|---|---|---|
| Mann-Whitney U | 0.34ms | 0.47ms |
| Bootstrap CI (1,000 resamples) | 26ms | 31ms |
| Full compare() statistical overhead | ~27ms | ~32ms |

Reproduce:

```bash
uv run pytest benchmarks/test_stat_overhead.py --benchmark-only -v
```

Numbers will vary by hardware. The key claim: statistical overhead is never the bottleneck. Even at n=1,000 per version, statistics complete in ~32ms while agent calls at typical LLM API latency (200ms to 2s per call) take 10 to 100 seconds.

On GitHub Actions (ubuntu-latest), expect 2-5x slower than M3 Pro due to different CPU architecture and shared resource contention.

---

## Tau-bench pass^k (`test_tau_bench.py`)

Measures agent reliability across k independent attempts per task.

**What pass^k means:** pass^k is the probability that an agent succeeds on at least one attempt out of k runs. It captures reliability degradation that single-run benchmarks miss entirely.

**Mock agent at 60% single-attempt success rate:**

| k | pass^k (formula) | Measured |
|---|---|---|
| 1 | 0.60 | ~0.60 |
| 4 | 1 - (0.4)^4 = 0.974 | ~0.97 |
| 8 | 1 - (0.4)^8 = 0.9993 | ~0.999 |

The k=1 headline number is insufficient. An agent that succeeds 60% of the time at k=1 looks unreliable; the same agent at k=8 succeeds 99.9% of the time. Single-run benchmarks measure k=1 only. agent-eval measures the full curve.

To use with a real agent, replace `_mock_agent()` with your agent callable. The harness handles the k-repetition loop.

```bash
uv run pytest benchmarks/test_tau_bench.py -v
```

---

## GAIA Level 1-3 split (`test_gaia.py`)

Accuracy stratified by task difficulty (GAIA Level 1 = straightforward, Level 3 = multi-hop with tool use).

**Why this matters:** A tool that scores 80% on Level 1 and 20% on Level 3 is very different from a tool that scores 50% uniformly. Single-number accuracy hides this. Per-level stratification shows capability boundaries honestly.

**Mock agent (configurable error rates per level):**

| Level | Mock agent | Notes |
|---|---|---|
| 1 | ~85% | Low-difficulty tasks |
| 2 | ~65% | Medium-difficulty, multi-step |
| 3 | ~35% | High-difficulty, multi-hop with tool use |

```bash
uv run pytest benchmarks/test_gaia.py -v
```

---

## SWE-bench scaffold score (`test_swebench.py`)

Measures the evaluation harness contribution to SWE-bench Verified resolved rate. The scaffold is the test case runner, output parser, and verdict logic -- not the underlying model.

**What scaffold score measures:** The same underlying model can show different resolved rates depending on evaluation harness quality. A better harness (clearer task prompts, better tool wiring, more reliable output parsing) lifts pass rates by 5-15 percentage points.

Replace the mock agent with a real code-generation agent to measure scaffold lift on your setup.

```bash
uv run pytest benchmarks/test_swebench.py -v
```

---

## Interpreting benchmark output

The `--benchmark-only` flag runs pytest-benchmark and skips regular test assertions. Use `-v` for per-test timing. Use `--benchmark-json=output.json` to save results for comparison across runs.

To compare against the committed baseline:

```bash
uv run pytest benchmarks/test_stat_overhead.py --benchmark-compare
```
