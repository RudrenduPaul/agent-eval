# agent-regress-cli

Statistical regression testing for LLM agents, from the command line or `npx`.

This is a thin Node.js wrapper around the [`agent-regress-cli`](https://pypi.org/project/agent-regress-cli/) Python package (its console command is `agent-regress`; the PyPI distribution is named `agent-regress-cli` since `agent-regress` was blocked as too similar to an unrelated existing project) -- the actual statistics (Mann-Whitney U, bootstrap confidence interval, Cohen's d) run in Python, so you need Python installed too:

```bash
pip install agent-regress-cli
```

(`uv tool install agent-regress-cli` or `pipx install agent-regress-cli` also work, and this wrapper will fall back to `uvx`/`pipx` automatically if the `agent-regress` command isn't on your `PATH`.)

## Install

```bash
npm install -g agent-regress-cli
```

Or run it without installing:

```bash
npx agent-regress-cli --help
```

## Usage

```bash
npx agent-regress-cli compare \
  --version-a-results version_a_scores.json \
  --version-b-results version_b_scores.json \
  --metric task_success_rate \
  --json
```

Each `--version-*-results` file is a JSON array of per-run scores, e.g. `[0.82, 0.79, 0.91]`. `--json` prints a single machine-readable JSON object to stdout (verdict, p-value, Cohen's d, confidence interval) -- built for agents and CI scripts to parse.

## FAQ

**Does this need Python installed?** Yes. This package only forwards your command to the real
`agent-regress` Python CLI -- it doesn't reimplement anything. If a working Python toolchain
(`pip`, `uv`, or `pipx`) isn't found, the command prints an actionable error telling you what to
install rather than failing silently.

**How is this different from Promptfoo, DeepEval, or Braintrust?** Those test whether a single
response clears a fixed quality threshold. `agent-regress` answers a different question: whether
an agent's behavior actually shifted between two versions, with a Mann-Whitney U p-value, a
bootstrap confidence interval, and a Cohen's d effect size -- not just a pass/fail on one run.

**Is it safe to run?** It never calls an LLM or makes a network request itself -- `compare()` takes
two callables (or two JSON files of pre-computed scores) you provide and runs pure-Python
statistics (scipy) over them. No API keys to configure.

## Docs

Full documentation, the Python API, and the statistics methodology live in the main repo:

https://github.com/RudrenduPaul/agent-eval
