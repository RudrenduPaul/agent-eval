"""Minimal leaderboard web server — stdlib only, no extra deps.

Reads leaderboard/results/*.json and serves an HTML table at :8080.
"""

from __future__ import annotations

import http.server
import json
import pathlib
import socketserver
from datetime import datetime

PORT = 8080
RESULTS_DIR = pathlib.Path("leaderboard/results")


def _load_results() -> list[dict]:
    results = []
    for f in sorted(RESULTS_DIR.glob("*.json"), reverse=True):
        try:
            with open(f) as fp:
                results.append(json.load(fp))
        except (json.JSONDecodeError, OSError):
            continue
    return results


def _render_row(r: dict) -> str:
    tau = r.get("tau_bench", {})
    gaia = r.get("gaia", {})
    swe = r.get("swebench", {})

    tau_k1 = f"{tau.get('pass_at_1', '—'):.3f}" if isinstance(tau.get("pass_at_1"), float) else "—"
    tau_k4 = f"{tau.get('pass_at_4', '—'):.3f}" if isinstance(tau.get("pass_at_4"), float) else "—"
    tau_k8 = f"{tau.get('pass_at_8', '—'):.3f}" if isinstance(tau.get("pass_at_8"), float) else "—"
    gaia_l1 = f"{gaia.get('level_1_accuracy', '—'):.3f}" if isinstance(gaia.get("level_1_accuracy"), float) else "—"
    gaia_l2 = f"{gaia.get('level_2_accuracy', '—'):.3f}" if isinstance(gaia.get("level_2_accuracy"), float) else "—"
    gaia_l3 = f"{gaia.get('level_3_accuracy', '—'):.3f}" if isinstance(gaia.get("level_3_accuracy"), float) else "—"
    swe_rate = f"{swe.get('scaffold_pass_rate', '—'):.3f}" if isinstance(swe.get("scaffold_pass_rate"), float) else "—"

    return f"""
        <tr>
            <td>{r.get("model_name", "—")}</td>
            <td>{r.get("framework", "—")}</td>
            <td>{r.get("submitted_date", "—")}</td>
            <td>{tau_k1}</td>
            <td>{tau_k4}</td>
            <td>{tau_k8}</td>
            <td>{gaia_l1}</td>
            <td>{gaia_l2}</td>
            <td>{gaia_l3}</td>
            <td>{swe_rate}</td>
        </tr>"""


def _render_page(results: list[dict]) -> str:
    rows = "".join(_render_row(r) for r in results) if results else \
        "<tr><td colspan='10' style='text-align:center;color:#888'>No results yet — submit via PR</td></tr>"
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>agent-eval leaderboard</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
          background: #f9f9f9; color: #222; padding: 2rem; }}
  h1 {{ font-size: 1.5rem; margin-bottom: 0.25rem; }}
  .sub {{ color: #666; font-size: 0.875rem; margin-bottom: 1.5rem; }}
  table {{ width: 100%; border-collapse: collapse; background: #fff;
           box-shadow: 0 1px 3px rgba(0,0,0,.12); border-radius: 6px;
           overflow: hidden; font-size: 0.875rem; }}
  th {{ background: #1a1a1a; color: #fff; padding: 0.6rem 0.8rem;
        text-align: left; font-weight: 600; white-space: nowrap; }}
  td {{ padding: 0.55rem 0.8rem; border-bottom: 1px solid #eee; }}
  tr:last-child td {{ border-bottom: none; }}
  tr:hover td {{ background: #f5f5f5; }}
  .group {{ background: #333; color: #aaa; font-size: 0.75rem;
            text-transform: uppercase; letter-spacing: .05em; }}
  footer {{ margin-top: 1.5rem; font-size: 0.8rem; color: #888; }}
  a {{ color: #0066cc; }}
</style>
</head>
<body>
<h1>agent-eval leaderboard</h1>
<p class="sub">
  Statistical regression testing for LLM agents &nbsp;·&nbsp;
  <a href="https://github.com/RudrenduPaul/agent-eval">GitHub</a> &nbsp;·&nbsp;
  Submit results via PR to <code>leaderboard/results/</code>
</p>
<table>
<thead>
  <tr>
    <th rowspan="2">Model</th>
    <th rowspan="2">Framework</th>
    <th rowspan="2">Date</th>
    <th colspan="3" class="group">Tau-bench pass^k</th>
    <th colspan="3" class="group">GAIA accuracy</th>
    <th rowspan="2">SWE-bench resolved</th>
  </tr>
  <tr>
    <th>k=1</th><th>k=4</th><th>k=8</th>
    <th>L1</th><th>L2</th><th>L3</th>
  </tr>
</thead>
<tbody>
{rows}
</tbody>
</table>
<footer>Last refreshed: {now} &nbsp;·&nbsp; Reload page to update</footer>
</body>
</html>"""


class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        results = _load_results()
        body = _render_page(results).encode()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt: str, *args: object) -> None:
        pass  # suppress per-request noise


if __name__ == "__main__":
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print(f"Leaderboard at http://localhost:{PORT}  (Ctrl+C to stop)")
        httpd.serve_forever()
