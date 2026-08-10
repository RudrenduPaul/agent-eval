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
import sys
from typing import Any

from mcp.server import MCPServer

_CLI_BIN = "agent-regress"


def _cli_help_text() -> str:
    """Capture ``agent-regress --help`` to use as the live tool description.

    Falls back to a short static description if the CLI can't be invoked
    (e.g. not on PATH yet at import time) -- this must never raise, since
    it runs at server-build time before any tool call has happened.
    """
    try:
        proc = subprocess.run(
            [_CLI_BIN, "--help"],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
        help_text = proc.stdout.strip() or proc.stderr.strip()
        if help_text:
            return help_text
    except (OSError, subprocess.TimeoutExpired) as exc:
        print(f"agent-regress-mcp: warning: could not capture --help: {exc}", file=sys.stderr)
    return "Run the agent-regress CLI (statistical regression testing for LLM agents)."


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


def build_app() -> MCPServer:
    app = MCPServer("agent-regress")
    tool_description = (
        f"Run the agent-regress CLI with the given arguments and return its "
        f"--json output, parsed. Real CLI --help output:\n\n{_cli_help_text()}"
    )

    @app.tool(description=tool_description)
    def run(args: list[str]) -> dict[str, Any]:
        return _run_impl(args)

    return app


def main() -> None:
    """Start the MCP server on stdio transport."""
    app = build_app()
    app.run(transport="stdio")


if __name__ == "__main__":
    main()
