# CLAUDE.md -- agentregress

## Git Workflow

When asked to commit, push, or "update GitHub" -- just do it. No questions.

- git add relevant files -> git commit -> git push origin main
- "commit" means commit AND push -- always both
- Never ask "should I push?"

Every commit message must end with:

Built by Rudrendu Paul and Sourav Nandy, developed with Claude Code

Never use Co-Authored-By: lines.

## Project Overview

agentregress: Python statistical regression testing framework for LLM agents.

Core angle: run agent N times at version A, N times at version B, apply
Mann-Whitney U + bootstrap CI, report p-value and Cohen's d.

A/B testing for agent quality. Not DeepEval (threshold-based). Not single-run
benchmarks. Statistical comparison of two version distributions.

License: Apache 2.0 core.
Primary integrations: LangGraph (P0), OpenAI Agents SDK (P0).

## Repo Layout

src/agent_regress/
- core/: runner.py, scorer.py, report.py, compare.py
- stats/: mann_whitney.py, bootstrap.py, effect_size.py (pure Python + scipy ONLY)
- integrations/: lazy-imported optional deps
- ci/: gate.py (AssertionError when p < threshold AND d > min_effect)
- benchmarks/: tau_bench.py, gaia.py, swebench.py
tests/unit/: no LLM calls
tests/integration/: real APIs, tagged @pytest.mark.integration
benchmarks/: standalone scripts
leaderboard/: git-committed JSON results

## Engineering Standards

uv run ruff check src/ tests/ benchmarks/
uv run ruff format --check src/ tests/ benchmarks/
uv run mypy src/ --strict
uv run pytest tests/unit/ --cov=src/ --cov-fail-under=80

## Key Invariants

- stats/ has ZERO LLM calls. Pure Python + scipy on lists of floats.
- runner.py: any callable dict->float. No framework coupling.
- gate.py: AssertionError when p < threshold AND d > min_effect.
- gate.py: WARN (not fail) when n < 30.
- All public API in __init__.py.
- mypy --strict must pass.
- leaderboard/results/ schema-validated in CI.

## Session Start

1. git status && git log --oneline -5
2. uv run pytest tests/unit/ -q
3. Read docs/lessons.md

## Anti-Sycophancy

- No performance claims without benchmark output
- stats/ is a scipy one-liner -- not the moat
- The moat is leaderboard governance and hosted regression history
- Braintrust closes the p-value gap in one sprint -- say this proactively
