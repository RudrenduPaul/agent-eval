"""Tests for web/serve.py's leaderboard rendering."""

from __future__ import annotations

import importlib.util
import pathlib

_SERVE_PATH = pathlib.Path(__file__).parents[2] / "web" / "serve.py"
_spec = importlib.util.spec_from_file_location("serve", _SERVE_PATH)
serve = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(serve)


def test_render_row_escapes_html_in_submitted_fields():
    malicious_result = {
        "model_name": "<script>alert(1)</script>",
        "framework": "<img src=x onerror=alert(2)>",
        "submitted_date": '2026-07-18"><b>injected</b>',
    }
    row = serve._render_row(malicious_result)
    assert "<script>" not in row
    assert "<img" not in row
    assert "&lt;script&gt;" in row
    assert "&lt;img" in row


def test_render_row_still_shows_the_real_values_once_escaped():
    result = {"model_name": "GPT-5 & friends", "framework": "LangGraph"}
    row = serve._render_row(result)
    assert "GPT-5 &amp; friends" in row
    assert "LangGraph" in row


def test_render_row_falls_back_to_em_dash_for_missing_fields():
    row = serve._render_row({})
    assert row.count("—") >= 3
