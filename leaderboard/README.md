# agent-eval Leaderboard

This directory tracks Tau-bench pass^k, GAIA, and SWE-bench results across
models and frameworks.

## Submit results

Open a PR adding a JSON file to `leaderboard/results/` that matches the schema
in `leaderboard/schema.json`. CI validates the schema automatically.

Results are reproduced independently before merging. Include a reproduction
command that runs in under 30 minutes.

## Schema

Required fields (see `leaderboard/schema.json`):
- model_name: Model or agent name and version
- framework: Framework used (LangGraph, OpenAI Agents SDK, etc.)
- submitted_by: GitHub handle
- submitted_date: YYYY-MM-DD format
- reproduction_command: Command to reproduce in under 30 minutes

## Methodology

**Tau-bench pass^k:** Run agent k times per task. Report fraction where agent
succeeded at least once. We report k=1, k=4, k=8.

**GAIA:** Run on GAIA validation set. Report accuracy by difficulty level (1, 2, 3).

**SWE-bench:** Report resolved rate on SWE-bench Verified using the agent-eval
scaffold harness.
