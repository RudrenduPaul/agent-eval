# agent-regress-npm-cli

Statistical regression testing for LLM agents, from the command line or `npx`.

This is a thin Node.js wrapper around the [`agent-regress-cli`](https://pypi.org/project/agent-regress-cli/) Python package (its console command is `agent-regress`; the PyPI distribution is named `agent-regress-cli` since `agent-regress` was blocked as too similar to an unrelated existing project) -- the actual statistics (Mann-Whitney U, bootstrap confidence interval, Cohen's d) run in Python, so you need Python installed too:

```bash
pip install agent-regress-cli
```

(`uv tool install agent-regress-cli` or `pipx install agent-regress-cli` also work, and this wrapper will fall back to `uvx`/`pipx` automatically if the `agent-regress` command isn't on your `PATH`.)

## Install

```bash
npm install -g agent-regress-npm-cli
```

Or run it without installing:

```bash
npx agent-regress-npm-cli --help
```

## Usage

```bash
npx agent-regress-npm-cli compare \
  --version-a-results version_a_scores.json \
  --version-b-results version_b_scores.json \
  --metric task_success_rate \
  --json
```

Each `--version-*-results` file is a JSON array of per-run scores, e.g. `[0.82, 0.79, 0.91]`. `--json` prints a single machine-readable JSON object to stdout (verdict, p-value, Cohen's d, confidence interval) -- built for agents and CI scripts to parse.

## Docs

Full documentation, the Python API, and the statistics methodology live in the main repo:

https://github.com/RudrenduPaul/agent-eval
