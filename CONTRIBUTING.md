# Contributing to agent-eval

Thanks for your interest. This covers everything to go from zero to a merged PR.

## Fastest path

1. Clone and run dev setup below
2. Pick an issue labeled `good first issue`
3. Open a draft PR early -- we can save you wasted work
4. Mark ready for review when tests pass

We aim to review PRs within 72 hours (weekdays).

## Dev setup

```bash
git clone https://github.com/RudrenduPaul/agent-eval
cd agent-eval
pip install uv
uv sync --extra dev
pre-commit install
uv run pytest tests/unit/ -q  # should pass 100% on a clean clone
```

## Engineering standards

Before submitting:

```bash
uv run ruff check src/ tests/ benchmarks/
uv run ruff format --check src/ tests/ benchmarks/
uv run mypy src/ --strict
uv run pytest tests/unit/ --cov=src/ --cov-fail-under=80
```

## What makes a PR merge quickly

- Tests added for every behavior change
- CHANGELOG entry for any user-facing change
- One focused change per PR

## What we will not merge

- PRs that break existing tests without a documented reason
- AI-generated code submitted without running and validating the output
- `CLAUDE.md`, `TODOS.md`, `BRANCH_PROTECTION.md`, or any `docs/security-review-*`,
  `docs/launch/*`, or `*preprint*` file -- these are internal build artifacts and
  must never land in this repo, even from a stale local branch
- Code comments or docs prose that cite an internal review/approval process by
  name (e.g. "per eng-review", "per the CEO review") instead of stating the
  engineering rationale directly

## Maintainer SLAs

- Bug reports: acknowledged within 24 hours (weekdays)
- Feature requests: triage label within 72 hours
- PRs: first review within 72 hours
- Security: acknowledged within 48 hours

## Community

Discord: discord.gg/agent-eval (#contributing channel)
