"""MCP server: exposes the ``agent-regress`` CLI as a single agent-callable tool.

Generic MCP wrapper pattern (pilot build, validated against this repo before
being stamped across the rest of the portfolio): one tool, ``run``, that
shells out to the real ``agent-regress`` console script with the caller's
args plus ``--json`` appended, parses the resulting JSON, and returns it.
The wrapper adds no new logic of its own -- it is a thin subprocess bridge,
so agent-callable behavior stays identical to running the CLI by hand.

Requires the `mcp` extra (`pip install "agent-regress-cli[mcp]"`). Started
via the ``agent-regress-mcp`` console script (stdio transport).

Uses ``mcp.server.MCPServer``, the official Python SDK's current high-level
server class (``mcp`` 2.0.0+). Earlier ``mcp`` 1.x releases exposed the same
``.tool()``/``.run()`` pattern under ``mcp.server.fastmcp.FastMCP`` -- that
module was removed in the 2.0.0 release. If a future ``mcp`` major version
renames this again, this is the one file that needs to change.

stdout is reserved for the JSON-RPC protocol the stdio transport speaks, so
nothing here prints to stdout directly -- the only stdout write happens
inside the CLI subprocess itself, and even that is captured (not inherited)
rather than passed through.
"""

from __future__ import annotations

import json
import subprocess
from typing import Any

from mcp.server import MCPServer

_CLI_BIN = "agent-regress"


def _run_impl(args: list[str]) -> dict[str, Any]:
    """Shell out to `agent-regress <args> --json` and return the parsed result.

    `args` should include the subcommand and its flags, e.g.
    ["compare", "--version-a-results", "a.json", "--version-b-results", "b.json"].
    `--json` is appended automatically if not already present. Module-level
    (not a closure) so it can be imported and called directly in tests,
    without going through a real MCP client/transport.
    """
    full_args = [*args] if "--json" in args else [*args, "--json"]
    try:
        proc = subprocess.run(
            [_CLI_BIN, *full_args],
            capture_output=True,
            text=True,
            timeout=120,
            check=False,
        )
    except OSError as exc:
        return {"error": f"failed to launch {_CLI_BIN}: {exc}"}

    if proc.returncode not in (0, 1):
        # 1 is a legitimate non-error exit for `compare --fail-on-regression`
        # on a REGRESSED verdict; anything else is a real failure.
        return {
            "error": f"{_CLI_BIN} exited {proc.returncode}",
            "stderr": proc.stderr.strip(),
        }

    try:
        return dict(json.loads(proc.stdout))
    except json.JSONDecodeError as exc:
        return {
            "error": f"could not parse {_CLI_BIN} --json output: {exc}",
            "stdout": proc.stdout,
            "stderr": proc.stderr.strip(),
        }


_TOOL_DESCRIPTION = """\
Run the agent-regress CLI as a subprocess and return its parsed --json output, \
so an agent can get a statistically grounded verdict on whether an LLM agent's \
behavior actually shifted between two versions instead of eyeballing two numbers.

Call this after you already have two pre-computed sets of per-run scores (one \
JSON array of numbers per agent version, produced by whatever harness ran each \
version) and you need to know whether the difference between them is a real \
regression/improvement or just run-to-run noise. Do not call it to generate \
those scores in the first place -- it only compares numbers that already exist \
on disk. Right now the CLI has one subcommand, `compare`; pass ["--help"] or \
["compare", "--help"] as `args` to discover any subcommands/flags added since \
this description was written.

Behavior: this is a read-only, idempotent operation with no network calls -- it \
spawns a local subprocess, reads the two score files you point it at, and writes \
nothing to disk itself. No API keys or network access are required, but the \
paths passed via --version-a-results/--version-b-results must already exist and \
contain valid JSON arrays of numbers. On a normal run (including a REGRESSED \
verdict with --fail-on-regression, which legitimately exits 1) the tool returns \
the CLI's parsed JSON report. On an actual failure (bad args, CLI not on PATH, \
unparseable output) it instead returns a dict with an "error" key and, where \
available, the captured "stderr"/"stdout".

Parameters:
    args: list[str] -- CLI argv, NOT a shell string. Include the subcommand and \
        its flags exactly as `agent-regress` would take them on the command \
        line; `--json` is appended automatically if you omit it. Examples:
        ["compare", "--version-a-results", "a.json", "--version-b-results", "b.json"]
        ["compare", "--version-a-results", "a.json", "--version-b-results", "b.json",
         "--metric", "tool_accuracy", "--min-effect", "0.3", "--fail-on-regression"]
        ["compare", "--help"]

Returns (JSON object) on success: metric, verdict (one of REGRESSED / STABLE / \
IMPROVED / INSUFFICIENT_DATA), p_value, effect_size, ci_lower, ci_upper, n_a, \
n_b, mean_a, mean_b, std_a, std_b, mean_delta, p_threshold, min_effect, and \
warnings (e.g. low sample size). On failure: error (and stderr/stdout when \
captured).\
"""


def build_app() -> MCPServer:
    app = MCPServer("agent-regress")

    @app.tool(description=_TOOL_DESCRIPTION)
    def run(args: list[str]) -> dict[str, Any]:
        return _run_impl(args)

    return app


def main() -> None:
    """Start the MCP server on stdio transport."""
    app = build_app()
    app.run(transport="stdio")


if __name__ == "__main__":
    main()
