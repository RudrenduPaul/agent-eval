# Benchmark Reproduction

Statistical test overhead — time to run the comparison itself, not the agent calls.

Measured on Apple M3 Pro, Python 3.14, scipy 1.15, numpy 2.2:

| Operation | n=50 per version | n=1,000 per version |
|---|---|---|
| Mann-Whitney U | **0.34ms** | **0.47ms** |
| Bootstrap CI (1,000 resamples) | **26ms** | **31ms** |
| Full compare() statistical overhead | **~27ms** | **~32ms** |

To reproduce:

```bash
git clone https://github.com/RudrenduPaul/agent-eval
cd agent-eval
uv sync --extra dev
uv run pytest benchmarks/test_stat_overhead.py --benchmark-only -v
```
